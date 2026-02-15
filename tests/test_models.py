from datetime import datetime

import pytest

from src.models import (
    Email,
    EmailAddress,
    EmailCategory,
    EmailThread,
    SendEmailRequest,
)


class TestEmailAddress:
    def test_email_address_str_with_name(self):
        addr = EmailAddress(email="test@example.com", name="Test User")
        assert str(addr) == "Test User <test@example.com>"

    def test_email_address_str_without_name(self):
        addr = EmailAddress(email="test@example.com")
        assert str(addr) == "test@example.com"


class TestEmail:
    def test_email_creation(self, sample_email):
        assert sample_email.id == "12345"
        assert sample_email.subject == "Test Email Subject"
        assert sample_email.is_read is False

    def test_email_serialization(self, sample_email):
        data = sample_email.model_dump()
        assert data["id"] == "12345"
        assert data["subject"] == "Test Email Subject"
        assert "from_address" in data


class TestEmailCategory:
    def test_category_values(self):
        assert EmailCategory.WORK.value == "Work"
        assert EmailCategory.PERSONAL.value == "Personal"
        assert EmailCategory.NEWSLETTERS.value == "Newsletters"
        assert EmailCategory.SPAM.value == "Spam"
        assert EmailCategory.NOTIFICATIONS.value == "Notifications"


class TestSendEmailRequest:
    def test_send_request_minimal(self):
        request = SendEmailRequest(
            account="test@gmail.com",
            to=["recipient@example.com"],
            subject="Test",
            body="Hello",
        )
        assert request.cc == []
        assert request.bcc == []
        assert request.html is False

    def test_send_request_full(self):
        request = SendEmailRequest(
            account="test@gmail.com",
            to=["recipient@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            subject="Test",
            body="<h1>Hello</h1>",
            html=True,
        )
        assert len(request.cc) == 1
        assert request.html is True
