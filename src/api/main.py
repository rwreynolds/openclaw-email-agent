from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..config import get_settings, setup_logging
from .dependencies import get_account_manager, get_openclaw_client, get_scheduler
from .error_handlers import register_error_handlers
from .routes import accounts, ai, emails, health, threads


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)

    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()

    yield

    # Shutdown
    scheduler.stop()
    await get_openclaw_client().close()
    get_account_manager().disconnect_all()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="OpenClaw Email Agent",
        description="Email agent for OpenClaw Gateway with Gmail IMAP/SMTP support",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register error handlers
    register_error_handlers(app)

    # Include routers
    app.include_router(health.router)
    app.include_router(accounts.router)
    app.include_router(emails.router)
    app.include_router(threads.router)
    app.include_router(ai.router)

    return app


app = create_app()
