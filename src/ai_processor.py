import logging
from typing import Optional

from .config import get_settings
from .models import ClassificationResult, Email, EmailCategory, SummaryResult
from .openclaw_client import OpenClawClient

logger = logging.getLogger(__name__)


class AIProcessor:
    def __init__(self, openclaw_client: OpenClawClient):
        self.client = openclaw_client
        self._categories = get_settings().get_categories()

    async def summarize(self, email: Email) -> SummaryResult:
        logger.info(f"Summarizing email {email.id}")

        summary = await self.client.summarize_email(email)

        if summary:
            email.summary = summary
            logger.info(f"Email {email.id} summarized")
        else:
            summary = self._fallback_summary(email)
            email.summary = summary
            logger.warning(f"Using fallback summary for email {email.id}")

        return SummaryResult(
            email_id=email.id,
            summary=summary,
        )

    async def classify(self, email: Email) -> ClassificationResult:
        logger.info(f"Classifying email {email.id}")

        category_str = await self.client.classify_email(email, self._categories)

        if category_str:
            try:
                category = EmailCategory(category_str)
            except ValueError:
                category = EmailCategory.UNKNOWN
        else:
            category = self._fallback_classify(email)

        email.classification = category
        logger.info(f"Email {email.id} classified as {category.value}")

        return ClassificationResult(
            email_id=email.id,
            category=category,
            confidence=1.0 if category_str else 0.5,
        )

    async def process(self, email: Email) -> tuple[SummaryResult, ClassificationResult]:
        summary_result = await self.summarize(email)
        classification_result = await self.classify(email)
        return summary_result, classification_result

    async def process_batch(
        self,
        emails: list[Email],
    ) -> list[tuple[SummaryResult, ClassificationResult]]:
        results = []
        for email in emails:
            try:
                result = await self.process(email)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing email {email.id}: {e}")
        return results

    def _fallback_summary(self, email: Email) -> str:
        """Generate a basic summary when LLM is unavailable."""
        from_name = email.from_address.name or email.from_address.email
        snippet = email.snippet or ""
        if len(snippet) > 100:
            snippet = snippet[:100] + "..."
        return f"Email from {from_name}: {snippet}"

    def _fallback_classify(self, email: Email) -> EmailCategory:
        """Classify using simple heuristics when LLM is unavailable."""
        subject_lower = email.subject.lower()
        from_email = email.from_address.email.lower()
        body = (email.body_plain or "").lower()

        # Check for newsletters/marketing
        newsletter_keywords = ["unsubscribe", "newsletter", "weekly digest", "update from"]
        if any(kw in body for kw in newsletter_keywords):
            return EmailCategory.NEWSLETTERS

        # Check for notifications
        notification_domains = ["noreply", "no-reply", "notifications", "notify", "alert"]
        if any(nd in from_email for nd in notification_domains):
            return EmailCategory.NOTIFICATIONS

        # Check for spam indicators
        spam_keywords = ["winner", "prize", "urgent action", "click here now", "limited time"]
        if any(kw in subject_lower or kw in body for kw in spam_keywords):
            return EmailCategory.SPAM

        # Check for work-related
        work_keywords = ["meeting", "deadline", "project", "report", "invoice", "schedule"]
        if any(kw in subject_lower for kw in work_keywords):
            return EmailCategory.WORK

        # Default to personal
        return EmailCategory.PERSONAL
