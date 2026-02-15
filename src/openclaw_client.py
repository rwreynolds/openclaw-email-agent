import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from .config import get_settings
from .models import Email, WebhookPayload

logger = logging.getLogger(__name__)


class OpenClawClient:
    def __init__(self):
        settings = get_settings()
        self.gateway_url = settings.openclaw_gateway_url
        self.webhook_url = settings.openclaw_webhook_url
        self.api_key = settings.openclaw_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def notify_new_emails(self, account: str, emails: list[Email]) -> bool:
        if not self.gateway_url:
            logger.warning("OpenClaw Gateway URL not configured, skipping webhook")
            return False

        payload = WebhookPayload(
            event="new_email",
            timestamp=datetime.utcnow(),
            account=account,
            emails=[
                {
                    "id": e.id,
                    "thread_id": e.thread_id,
                    "from": str(e.from_address),
                    "subject": e.subject,
                    "snippet": e.snippet,
                    "classification": e.classification.value if e.classification else None,
                    "received_at": e.received_at.isoformat(),
                }
                for e in emails
            ],
        )

        try:
            client = await self._get_client()
            response = await client.post(
                self.webhook_url,
                json=payload.model_dump(mode="json"),
            )
            response.raise_for_status()
            logger.info(f"Webhook sent for {len(emails)} new emails from {account}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    async def llm_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
    ) -> Optional[str]:
        if not self.gateway_url:
            logger.warning("OpenClaw Gateway URL not configured")
            return None

        # OpenClaw Gateway LLM endpoint
        llm_url = f"{self.gateway_url.rstrip('/')}/api/llm/completion"

        payload: dict[str, Any] = {
            "prompt": prompt,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            client = await self._get_client()
            response = await client.post(llm_url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("completion") or data.get("text") or data.get("content")
        except httpx.HTTPError as e:
            logger.error(f"LLM request failed: {e}")
            return None

    async def summarize_email(self, email: Email) -> Optional[str]:
        prompt = f"""Summarize the following email in 2-3 sentences:

From: {email.from_address}
Subject: {email.subject}
Date: {email.received_at}

{email.body_plain or email.body_html or '(no content)'}

Summary:"""

        return await self.llm_request(
            prompt=prompt,
            system_prompt="You are a helpful assistant that summarizes emails concisely.",
            max_tokens=200,
        )

    async def classify_email(self, email: Email, categories: list[str]) -> Optional[str]:
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following email into exactly one of these categories: {categories_str}

From: {email.from_address}
Subject: {email.subject}

{email.snippet or email.body_plain[:500] if email.body_plain else '(no content)'}

Category (respond with only the category name):"""

        result = await self.llm_request(
            prompt=prompt,
            system_prompt="You are an email classifier. Respond with only the category name, nothing else.",
            max_tokens=20,
        )

        if result:
            # Clean up response
            result = result.strip()
            # Find matching category (case insensitive)
            for cat in categories:
                if cat.lower() == result.lower():
                    return cat
            # Return first word if it matches
            first_word = result.split()[0] if result else None
            if first_word:
                for cat in categories:
                    if cat.lower() == first_word.lower():
                        return cat

        return None
