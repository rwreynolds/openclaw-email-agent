from unittest.mock import AsyncMock

import pytest

from src.ai_processor import AIProcessor
from src.models import EmailCategory


@pytest.fixture
def mock_openclaw():
    mock = AsyncMock()
    return mock


@pytest.fixture
def ai_processor(mock_openclaw):
    return AIProcessor(openclaw_client=mock_openclaw)


class TestAIProcessor:
    @pytest.mark.asyncio
    async def test_summarize_with_llm(self, ai_processor, mock_openclaw, sample_email):
        mock_openclaw.summarize_email.return_value = "Test summary from LLM"

        result = await ai_processor.summarize(sample_email)

        assert result.summary == "Test summary from LLM"
        assert sample_email.summary == "Test summary from LLM"
        mock_openclaw.summarize_email.assert_called_once_with(sample_email)

    @pytest.mark.asyncio
    async def test_summarize_fallback(self, ai_processor, mock_openclaw, sample_email):
        mock_openclaw.summarize_email.return_value = None

        result = await ai_processor.summarize(sample_email)

        assert "Test Sender" in result.summary
        assert sample_email.summary is not None

    @pytest.mark.asyncio
    async def test_classify_with_llm(self, ai_processor, mock_openclaw, sample_email):
        mock_openclaw.classify_email.return_value = "Work"

        result = await ai_processor.classify(sample_email)

        assert result.category == EmailCategory.WORK
        assert sample_email.classification == EmailCategory.WORK

    @pytest.mark.asyncio
    async def test_classify_fallback_newsletter(self, ai_processor, mock_openclaw, sample_email_newsletter):
        mock_openclaw.classify_email.return_value = None

        result = await ai_processor.classify(sample_email_newsletter)

        assert result.category == EmailCategory.NEWSLETTERS

    @pytest.mark.asyncio
    async def test_classify_fallback_work(self, ai_processor, mock_openclaw, sample_email_work):
        mock_openclaw.classify_email.return_value = None

        result = await ai_processor.classify(sample_email_work)

        assert result.category == EmailCategory.WORK

    @pytest.mark.asyncio
    async def test_process_both(self, ai_processor, mock_openclaw, sample_email):
        mock_openclaw.summarize_email.return_value = "Summary"
        mock_openclaw.classify_email.return_value = "Personal"

        summary_result, classification_result = await ai_processor.process(sample_email)

        assert summary_result.summary == "Summary"
        assert classification_result.category == EmailCategory.PERSONAL


class TestFallbackClassification:
    @pytest.mark.asyncio
    async def test_notification_detection(self, ai_processor, mock_openclaw):
        from datetime import datetime

        from src.models import Email, EmailAddress

        email = Email(
            id="1",
            account="test@gmail.com",
            message_id="<msg@test.com>",
            from_address=EmailAddress(email="noreply@service.com"),
            to_addresses=[],
            subject="Your order has shipped",
            body_plain="Your package is on the way.",
            received_at=datetime.now(),
        )
        mock_openclaw.classify_email.return_value = None

        result = await ai_processor.classify(email)

        assert result.category == EmailCategory.NOTIFICATIONS

    @pytest.mark.asyncio
    async def test_spam_detection(self, ai_processor, mock_openclaw):
        from datetime import datetime

        from src.models import Email, EmailAddress

        email = Email(
            id="1",
            account="test@gmail.com",
            message_id="<msg@test.com>",
            from_address=EmailAddress(email="winner@lottery.com"),
            to_addresses=[],
            subject="You are a WINNER! Claim your prize now!",
            body_plain="Click here now to claim your limited time prize!",
            received_at=datetime.now(),
        )
        mock_openclaw.classify_email.return_value = None

        result = await ai_processor.classify(email)

        assert result.category == EmailCategory.SPAM
