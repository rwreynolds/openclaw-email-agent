import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .account_manager import AccountManager
from .config import get_settings
from .models import Email
from .openclaw_client import OpenClawClient
from .thread_manager import ThreadManager

if TYPE_CHECKING:
    from .ai_processor import AIProcessor

logger = logging.getLogger(__name__)


class EmailScheduler:
    def __init__(
        self,
        account_manager: AccountManager,
        thread_manager: ThreadManager,
        openclaw_client: OpenClawClient,
        ai_processor: Optional["AIProcessor"] = None,
    ):
        self.account_manager = account_manager
        self.thread_manager = thread_manager
        self.openclaw_client = openclaw_client
        self.ai_processor = ai_processor
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._last_check: dict[str, datetime] = {}
        self._seen_ids: dict[str, set[str]] = {}
        self._enable_ai = True

    def start(self) -> None:
        if self._scheduler is not None:
            return

        settings = get_settings()
        interval_minutes = settings.poll_interval_minutes

        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._poll_emails,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="email_poll",
            name="Poll for new emails",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(f"Email scheduler started (polling every {interval_minutes} minutes)")

        # Run initial poll
        asyncio.create_task(self._poll_emails())

    def stop(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Email scheduler stopped")

    async def _poll_emails(self) -> None:
        logger.info("Polling for new emails...")

        accounts = self.account_manager.list_accounts()
        if not accounts:
            logger.warning("No accounts configured")
            return

        for account in accounts:
            try:
                await self._check_account(account.id, str(account.email))
            except Exception as e:
                logger.error(f"Error checking account {account.email}: {e}")

    async def _check_account(self, account_id: str, account_email: str) -> None:
        # Initialize seen IDs for this account
        if account_id not in self._seen_ids:
            self._seen_ids[account_id] = set()

        # Fetch recent unread emails
        emails = self.account_manager.fetch_unread(account_id=account_id, limit=50)

        if not emails:
            logger.debug(f"No unread emails for {account_email}")
            return

        # Find new emails (not seen before)
        new_emails: list[Email] = []
        for email in emails:
            if email.id not in self._seen_ids[account_id]:
                new_emails.append(email)
                self._seen_ids[account_id].add(email.id)

        if not new_emails:
            logger.debug(f"No new emails for {account_email}")
            return

        logger.info(f"Found {len(new_emails)} new emails for {account_email}")

        # Process emails with AI (classify)
        if self._enable_ai and self.ai_processor:
            for email in new_emails:
                try:
                    await self.ai_processor.classify(email)
                except Exception as e:
                    logger.error(f"AI classification failed for {email.id}: {e}")

        # Update thread manager
        for email in new_emails:
            self.thread_manager.add_email_to_thread(email)

        # Send webhook notification (includes classification if available)
        await self.openclaw_client.notify_new_emails(account_email, new_emails)

        # Update last check time
        self._last_check[account_id] = datetime.utcnow()

    async def force_poll(self) -> dict:
        await self._poll_emails()
        return {
            "status": "polled",
            "timestamp": datetime.utcnow().isoformat(),
            "accounts_checked": len(self.account_manager.list_accounts()),
        }

    def get_status(self) -> dict:
        return {
            "running": self._scheduler is not None and self._scheduler.running,
            "last_checks": {
                acc_id: ts.isoformat() for acc_id, ts in self._last_check.items()
            },
            "next_run": (
                self._scheduler.get_job("email_poll").next_run_time.isoformat()
                if self._scheduler and self._scheduler.get_job("email_poll")
                else None
            ),
        }
