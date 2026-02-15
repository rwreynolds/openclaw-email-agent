import json
import logging
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def sanitize_credential(value: str) -> str:
    """Remove invisible/problematic characters from credentials."""
    # Replace non-breaking spaces, zero-width spaces, and other invisible chars
    return (
        value.replace("\xa0", "")  # non-breaking space
        .replace("\u200b", "")  # zero-width space
        .replace("\u00a0", "")  # another non-breaking space
        .replace(" ", "")  # regular spaces (passwords shouldn't have them)
        .strip()
    )


class GmailAccountConfig:
    def __init__(self, email: str, app_password: str):
        self.email = email.strip()
        self.app_password = sanitize_credential(app_password)
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # OpenClaw Gateway
    openclaw_gateway_url: str = ""
    openclaw_webhook_endpoint: str = "/webhooks/email"
    openclaw_api_key: str = ""

    # Gmail Accounts (JSON string)
    gmail_accounts: str = "[]"

    # Polling
    poll_interval_minutes: int = 15

    # Classification
    email_categories: str = "Work,Personal,Newsletters,Spam,Notifications"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("gmail_accounts", mode="before")
    @classmethod
    def parse_gmail_accounts(cls, v: str) -> str:
        # Validate JSON format
        if isinstance(v, str) and v:
            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON for GMAIL_ACCOUNTS: {e}")
        return v

    def get_gmail_accounts(self) -> list[GmailAccountConfig]:
        accounts = json.loads(self.gmail_accounts)
        return [
            GmailAccountConfig(
                email=acc["email"],
                app_password=acc["app_password"],
            )
            for acc in accounts
        ]

    def get_categories(self) -> list[str]:
        return [cat.strip() for cat in self.email_categories.split(",")]

    @property
    def openclaw_webhook_url(self) -> str:
        return f"{self.openclaw_gateway_url.rstrip('/')}{self.openclaw_webhook_endpoint}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
