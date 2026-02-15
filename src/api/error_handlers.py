import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..exceptions import (
    AccountNotFoundError,
    AIProcessingError,
    AuthenticationError,
    ConnectionError,
    EmailAgentError,
    EmailNotFoundError,
    IMAPError,
    OpenClawError,
    SendEmailError,
    ThreadNotFoundError,
)

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AccountNotFoundError)
    async def account_not_found_handler(request: Request, exc: AccountNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error": "account_not_found", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(EmailNotFoundError)
    async def email_not_found_handler(request: Request, exc: EmailNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error": "email_not_found", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(ThreadNotFoundError)
    async def thread_not_found_handler(request: Request, exc: ThreadNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error": "thread_not_found", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        logger.error(f"Authentication error: {exc.message}")
        return JSONResponse(
            status_code=401,
            content={"error": "authentication_failed", "message": exc.message},
        )

    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request: Request, exc: ConnectionError):
        logger.error(f"Connection error: {exc.message}")
        return JSONResponse(
            status_code=503,
            content={"error": "connection_failed", "message": exc.message},
        )

    @app.exception_handler(SendEmailError)
    async def send_email_error_handler(request: Request, exc: SendEmailError):
        logger.error(f"Send email error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={"error": "send_failed", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(IMAPError)
    async def imap_error_handler(request: Request, exc: IMAPError):
        logger.error(f"IMAP error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={"error": "imap_error", "message": exc.message},
        )

    @app.exception_handler(OpenClawError)
    async def openclaw_error_handler(request: Request, exc: OpenClawError):
        logger.error(f"OpenClaw error: {exc.message}")
        return JSONResponse(
            status_code=502,
            content={"error": "openclaw_error", "message": exc.message},
        )

    @app.exception_handler(AIProcessingError)
    async def ai_error_handler(request: Request, exc: AIProcessingError):
        logger.warning(f"AI processing error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={"error": "ai_processing_failed", "message": exc.message},
        )

    @app.exception_handler(EmailAgentError)
    async def generic_agent_error_handler(request: Request, exc: EmailAgentError):
        logger.error(f"Email agent error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "An unexpected error occurred"},
        )
