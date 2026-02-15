import hashlib
import logging
from datetime import datetime
from typing import Optional

from .config import GmailAccountConfig, get_settings
from .imap_client import IMAPClient
from .models import Account, Email, SendEmailRequest
from .smtp_client import SMTPClient

logger = logging.getLogger(__name__)


class AccountManager:
    def __init__(self):
        self._accounts: dict[str, GmailAccountConfig] = {}
        self._imap_clients: dict[str, IMAPClient] = {}
        self._smtp_clients: dict[str, SMTPClient] = {}
        self._last_sync: dict[str, datetime] = {}
        self._load_accounts()

    def _load_accounts(self) -> None:
        settings = get_settings()
        for account in settings.get_gmail_accounts():
            self.add_account(account)

    def _generate_id(self, email: str) -> str:
        return hashlib.sha256(email.encode()).hexdigest()[:12]

    def add_account(self, config: GmailAccountConfig) -> Account:
        account_id = self._generate_id(config.email)
        self._accounts[account_id] = config
        logger.info(f"Added account: {config.email}")
        return Account(
            id=account_id,
            email=config.email,
            is_connected=False,
        )

    def remove_account(self, account_id: str) -> bool:
        if account_id not in self._accounts:
            return False

        # Disconnect clients if connected
        if account_id in self._imap_clients:
            self._imap_clients[account_id].disconnect()
            del self._imap_clients[account_id]

        if account_id in self._smtp_clients:
            self._smtp_clients[account_id].disconnect()
            del self._smtp_clients[account_id]

        del self._accounts[account_id]
        logger.info(f"Removed account: {account_id}")
        return True

    def list_accounts(self) -> list[Account]:
        accounts = []
        for account_id, config in self._accounts.items():
            accounts.append(
                Account(
                    id=account_id,
                    email=config.email,
                    is_connected=account_id in self._imap_clients,
                    last_sync_at=self._last_sync.get(account_id),
                )
            )
        return accounts

    def get_account(self, account_id: str) -> Optional[Account]:
        config = self._accounts.get(account_id)
        if not config:
            return None
        return Account(
            id=account_id,
            email=config.email,
            is_connected=account_id in self._imap_clients,
            last_sync_at=self._last_sync.get(account_id),
        )

    def get_account_by_email(self, email: str) -> Optional[tuple[str, GmailAccountConfig]]:
        for account_id, config in self._accounts.items():
            if config.email == email:
                return account_id, config
        return None

    def get_imap_client(self, account_id: str) -> Optional[IMAPClient]:
        if account_id not in self._accounts:
            return None

        if account_id not in self._imap_clients:
            config = self._accounts[account_id]
            client = IMAPClient(config)
            client.connect()
            self._imap_clients[account_id] = client

        return self._imap_clients[account_id]

    def get_smtp_client(self, account_id: str) -> Optional[SMTPClient]:
        if account_id not in self._accounts:
            return None

        if account_id not in self._smtp_clients:
            config = self._accounts[account_id]
            client = SMTPClient(config)
            client.connect()
            self._smtp_clients[account_id] = client

        return self._smtp_clients[account_id]

    def fetch_emails(
        self,
        account_id: Optional[str] = None,
        mailbox: str = "INBOX",
        criteria: str = "ALL",
        limit: int = 50,
    ) -> list[Email]:
        emails = []

        if account_id:
            # Fetch from specific account
            client = self.get_imap_client(account_id)
            if client:
                emails = client.fetch_emails(mailbox, criteria, limit)
                self._last_sync[account_id] = datetime.utcnow()
        else:
            # Fetch from all accounts
            for acc_id in self._accounts:
                client = self.get_imap_client(acc_id)
                if client:
                    account_emails = client.fetch_emails(mailbox, criteria, limit)
                    emails.extend(account_emails)
                    self._last_sync[acc_id] = datetime.utcnow()

        # Sort by date, newest first
        emails.sort(key=lambda e: e.received_at, reverse=True)
        return emails[:limit]

    def fetch_unread(
        self,
        account_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[Email]:
        return self.fetch_emails(
            account_id=account_id,
            criteria="UNSEEN",
            limit=limit,
        )

    def get_email(self, email_id: str, account_id: str) -> Optional[Email]:
        client = self.get_imap_client(account_id)
        if client:
            return client.fetch_email(email_id.encode())
        return None

    def send_email(self, request: SendEmailRequest) -> bool:
        result = self.get_account_by_email(str(request.account))
        if not result:
            logger.error(f"Account not found: {request.account}")
            return False

        account_id, _ = result
        client = self.get_smtp_client(account_id)
        if client:
            return client.send_email(request)
        return False

    def mark_read(self, email_id: str, account_id: str) -> bool:
        client = self.get_imap_client(account_id)
        if client:
            return client.mark_read(email_id)
        return False

    def mark_unread(self, email_id: str, account_id: str) -> bool:
        client = self.get_imap_client(account_id)
        if client:
            return client.mark_unread(email_id)
        return False

    def archive(self, email_id: str, account_id: str) -> bool:
        client = self.get_imap_client(account_id)
        if client:
            return client.archive(email_id)
        return False

    def delete(self, email_id: str, account_id: str) -> bool:
        client = self.get_imap_client(account_id)
        if client:
            return client.delete(email_id)
        return False

    def disconnect_all(self) -> None:
        for client in self._imap_clients.values():
            client.disconnect()
        for client in self._smtp_clients.values():
            client.disconnect()
        self._imap_clients.clear()
        self._smtp_clients.clear()
        logger.info("Disconnected all clients")
