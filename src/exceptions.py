class EmailAgentError(Exception):
    """Base exception for email agent."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(EmailAgentError):
    """Failed to authenticate with email server."""

    pass


class ConnectionError(EmailAgentError):
    """Failed to connect to email server."""

    pass


class AccountNotFoundError(EmailAgentError):
    """Account not found."""

    pass


class EmailNotFoundError(EmailAgentError):
    """Email not found."""

    pass


class ThreadNotFoundError(EmailAgentError):
    """Thread not found."""

    pass


class SendEmailError(EmailAgentError):
    """Failed to send email."""

    pass


class IMAPError(EmailAgentError):
    """IMAP operation failed."""

    pass


class OpenClawError(EmailAgentError):
    """OpenClaw Gateway communication error."""

    pass


class AIProcessingError(EmailAgentError):
    """AI processing failed."""

    pass
