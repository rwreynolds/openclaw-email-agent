from datetime import datetime

import pytest

from src.models import Email, EmailAddress
from src.thread_manager import ThreadManager


@pytest.fixture
def thread_manager():
    return ThreadManager()


@pytest.fixture
def emails_same_thread():
    """Create emails belonging to the same thread."""
    base_time = datetime(2026, 2, 14, 12, 0, 0)
    return [
        Email(
            id="1",
            account="test@gmail.com",
            thread_id="thread-001",
            message_id="<msg-1@gmail.com>",
            from_address=EmailAddress(email="alice@example.com", name="Alice"),
            to_addresses=[EmailAddress(email="test@gmail.com")],
            subject="Hello",
            body_plain="Hi there!",
            received_at=base_time,
            is_read=True,
        ),
        Email(
            id="2",
            account="test@gmail.com",
            thread_id="thread-001",
            message_id="<msg-2@gmail.com>",
            in_reply_to="<msg-1@gmail.com>",
            from_address=EmailAddress(email="test@gmail.com"),
            to_addresses=[EmailAddress(email="alice@example.com", name="Alice")],
            subject="Re: Hello",
            body_plain="Hello Alice!",
            received_at=datetime(2026, 2, 14, 13, 0, 0),
            is_read=True,
        ),
        Email(
            id="3",
            account="test@gmail.com",
            thread_id="thread-001",
            message_id="<msg-3@gmail.com>",
            in_reply_to="<msg-2@gmail.com>",
            from_address=EmailAddress(email="alice@example.com", name="Alice"),
            to_addresses=[EmailAddress(email="test@gmail.com")],
            subject="Re: Hello",
            body_plain="How are you?",
            received_at=datetime(2026, 2, 14, 14, 0, 0),
            is_read=False,
        ),
    ]


class TestThreadManager:
    def test_group_emails_by_thread(self, thread_manager, emails_same_thread):
        threads = thread_manager.group_emails_by_thread(emails_same_thread)

        assert len(threads) == 1
        thread = threads[0]
        assert thread.id == "thread-001"
        assert thread.email_count == 3
        assert thread.subject == "Hello"  # Original subject without Re:
        assert thread.has_unread is True  # One email is unread

    def test_thread_participants(self, thread_manager, emails_same_thread):
        threads = thread_manager.group_emails_by_thread(emails_same_thread)
        thread = threads[0]

        participant_emails = {p.email for p in thread.participants}
        assert "alice@example.com" in participant_emails
        assert "test@gmail.com" in participant_emails

    def test_get_thread(self, thread_manager, emails_same_thread):
        thread_manager.group_emails_by_thread(emails_same_thread)

        thread = thread_manager.get_thread("thread-001")
        assert thread is not None
        assert thread.id == "thread-001"

    def test_get_thread_not_found(self, thread_manager):
        thread = thread_manager.get_thread("nonexistent")
        assert thread is None

    def test_add_email_to_existing_thread(self, thread_manager, emails_same_thread):
        # Group initial emails
        thread_manager.group_emails_by_thread(emails_same_thread[:2])

        # Add new email to thread
        new_email = emails_same_thread[2]
        thread = thread_manager.add_email_to_thread(new_email)

        assert thread.email_count == 3
        assert thread.has_unread is True

    def test_add_email_creates_new_thread(self, thread_manager, sample_email):
        thread = thread_manager.add_email_to_thread(sample_email)

        assert thread is not None
        assert thread.email_count == 1

    def test_list_threads(self, thread_manager, emails_same_thread, sample_email):
        thread_manager.group_emails_by_thread(emails_same_thread)
        thread_manager.add_email_to_thread(sample_email)

        threads = thread_manager.list_threads()
        assert len(threads) == 2

    def test_list_threads_with_limit(self, thread_manager, emails_same_thread, sample_email):
        thread_manager.group_emails_by_thread(emails_same_thread)
        thread_manager.add_email_to_thread(sample_email)

        threads = thread_manager.list_threads(limit=1)
        assert len(threads) == 1

    def test_clear(self, thread_manager, emails_same_thread):
        thread_manager.group_emails_by_thread(emails_same_thread)
        assert len(thread_manager.list_threads()) > 0

        thread_manager.clear()
        assert len(thread_manager.list_threads()) == 0
