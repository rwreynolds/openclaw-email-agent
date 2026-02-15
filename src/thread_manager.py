import logging
from collections import defaultdict
from typing import Optional

from .models import Email, EmailAddress, EmailThread

logger = logging.getLogger(__name__)


class ThreadManager:
    def __init__(self):
        self._threads: dict[str, EmailThread] = {}
        self._email_to_thread: dict[str, str] = {}

    def group_emails_by_thread(self, emails: list[Email]) -> list[EmailThread]:
        threads_map: dict[str, list[Email]] = defaultdict(list)

        for email in emails:
            thread_id = email.thread_id or email.id
            threads_map[thread_id].append(email)
            self._email_to_thread[email.id] = thread_id

        threads = []
        for thread_id, thread_emails in threads_map.items():
            thread = self._create_thread(thread_id, thread_emails)
            self._threads[thread_id] = thread
            threads.append(thread)

        # Sort by latest email date
        threads.sort(key=lambda t: t.latest_email_at, reverse=True)
        return threads

    def _create_thread(self, thread_id: str, emails: list[Email]) -> EmailThread:
        # Sort emails by date
        emails.sort(key=lambda e: e.received_at)

        # Get unique participants
        participants_set: dict[str, EmailAddress] = {}
        for email in emails:
            addr = email.from_address
            if addr.email not in participants_set:
                participants_set[addr.email] = addr
            for to_addr in email.to_addresses:
                if to_addr.email not in participants_set:
                    participants_set[to_addr.email] = to_addr

        # Get subject from first email (original)
        subject = emails[0].subject if emails else ""
        # Remove Re: prefix for thread subject
        if subject.lower().startswith("re:"):
            subject = subject[3:].strip()

        # Check for unread
        has_unread = any(not e.is_read for e in emails)

        # Get account from first email
        account = emails[0].account if emails else ""

        return EmailThread(
            id=thread_id,
            account=account,
            subject=subject,
            participants=list(participants_set.values()),
            email_count=len(emails),
            emails=emails,
            latest_email_at=emails[-1].received_at if emails else emails[0].received_at,
            has_unread=has_unread,
        )

    def get_thread(self, thread_id: str) -> Optional[EmailThread]:
        return self._threads.get(thread_id)

    def get_thread_for_email(self, email_id: str) -> Optional[EmailThread]:
        thread_id = self._email_to_thread.get(email_id)
        if thread_id:
            return self._threads.get(thread_id)
        return None

    def add_email_to_thread(self, email: Email) -> EmailThread:
        thread_id = email.thread_id or email.id
        self._email_to_thread[email.id] = thread_id

        if thread_id in self._threads:
            thread = self._threads[thread_id]
            # Add email to existing thread
            thread.emails.append(email)
            thread.emails.sort(key=lambda e: e.received_at)
            thread.email_count = len(thread.emails)
            thread.latest_email_at = thread.emails[-1].received_at

            # Update participants
            existing_emails = {p.email for p in thread.participants}
            if email.from_address.email not in existing_emails:
                thread.participants.append(email.from_address)
            for to_addr in email.to_addresses:
                if to_addr.email not in existing_emails:
                    thread.participants.append(to_addr)

            # Update unread status
            thread.has_unread = any(not e.is_read for e in thread.emails)
        else:
            # Create new thread
            thread = self._create_thread(thread_id, [email])
            self._threads[thread_id] = thread

        return thread

    def list_threads(
        self,
        account: Optional[str] = None,
        limit: int = 50,
    ) -> list[EmailThread]:
        threads = list(self._threads.values())

        if account:
            threads = [t for t in threads if t.account == account]

        # Sort by latest email
        threads.sort(key=lambda t: t.latest_email_at, reverse=True)

        return threads[:limit]

    def clear(self) -> None:
        self._threads.clear()
        self._email_to_thread.clear()
