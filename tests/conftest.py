import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ["GMAIL_ACCOUNTS"] = '[]'
os.environ["OPENCLAW_GATEWAY_URL"] = "http://test-gateway:8080"
os.environ["OPENCLAW_API_KEY"] = "test-api-key"

from src.api.main import create_app
from src.config import GmailAccountConfig
from src.models import Email, EmailAddress, EmailCategory


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = create_app()
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
def mock_gmail_account():
    """Create a mock Gmail account configuration."""
    return GmailAccountConfig(
        email="test@gmail.com",
        app_password="test-password",
    )


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        id="12345",
        account="test@gmail.com",
        thread_id="thread-999",
        message_id="<msg-001@gmail.com>",
        from_address=EmailAddress(email="sender@example.com", name="Test Sender"),
        to_addresses=[EmailAddress(email="test@gmail.com", name="Test User")],
        subject="Test Email Subject",
        body_plain="This is a test email body.",
        snippet="This is a test email...",
        received_at=datetime(2026, 2, 14, 12, 0, 0),
        is_read=False,
    )


@pytest.fixture
def sample_email_work():
    """Create a sample work email for testing classification."""
    return Email(
        id="12346",
        account="test@gmail.com",
        thread_id="thread-002",
        message_id="<msg-002@gmail.com>",
        from_address=EmailAddress(email="boss@company.com", name="Boss"),
        to_addresses=[EmailAddress(email="test@gmail.com")],
        subject="Meeting tomorrow at 10am",
        body_plain="Please prepare the project report for the meeting.",
        snippet="Please prepare the project report...",
        received_at=datetime(2026, 2, 14, 13, 0, 0),
        is_read=False,
    )


@pytest.fixture
def sample_email_newsletter():
    """Create a sample newsletter email for testing classification."""
    return Email(
        id="12347",
        account="test@gmail.com",
        thread_id="thread-003",
        message_id="<msg-003@newsletter.com>",
        from_address=EmailAddress(email="news@newsletter.com", name="Weekly Digest"),
        to_addresses=[EmailAddress(email="test@gmail.com")],
        subject="Your Weekly Newsletter",
        body_plain="Here are this week's top stories. Click here to unsubscribe.",
        snippet="Here are this week's top stories...",
        received_at=datetime(2026, 2, 14, 14, 0, 0),
        is_read=True,
    )


@pytest.fixture
def mock_imap_connection():
    """Create a mock IMAP connection."""
    mock = MagicMock()
    mock.login.return_value = ("OK", [])
    mock.select.return_value = ("OK", [b"10"])
    mock.search.return_value = ("OK", [b"1 2 3"])
    mock.logout.return_value = ("OK", [])
    return mock


@pytest.fixture
def mock_smtp_connection():
    """Create a mock SMTP connection."""
    mock = MagicMock()
    mock.login.return_value = (235, b"Authentication successful")
    mock.sendmail.return_value = {}
    mock.quit.return_value = (221, b"Bye")
    return mock


@pytest.fixture
def mock_openclaw_client():
    """Create a mock OpenClaw client."""
    mock = AsyncMock()
    mock.notify_new_emails.return_value = True
    mock.summarize_email.return_value = "This is a test summary."
    mock.classify_email.return_value = "Work"
    mock.close.return_value = None
    return mock
