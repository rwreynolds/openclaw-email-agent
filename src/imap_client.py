import email
import imaplib
import logging
import re
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional

from .config import GmailAccountConfig
from .models import Attachment, Email, EmailAddress

logger = logging.getLogger(__name__)


def safe_str(value: str | bytes | None) -> str:
    """Convert any value to a safe ASCII-compatible string."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    # Replace non-breaking spaces and other problematic chars
    return value.replace("\xa0", " ").replace("\u200b", "")


class IMAPClient:
    def __init__(self, account: GmailAccountConfig):
        self.account = account
        self._connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        if self._connection:
            return
        logger.info(f"Connecting to IMAP server for {self.account.email}")
        self._connection = imaplib.IMAP4_SSL(
            self.account.imap_server,
            self.account.imap_port,
        )
        self._connection.login(self.account.email, self.account.app_password)
        logger.info(f"Connected to IMAP server for {self.account.email}")

    def disconnect(self) -> None:
        if self._connection:
            try:
                self._connection.logout()
            except Exception:
                pass
            self._connection = None
            logger.info(f"Disconnected from IMAP for {self.account.email}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _ensure_connected(self) -> imaplib.IMAP4_SSL:
        if not self._connection:
            self.connect()
        return self._connection  # type: ignore

    def list_mailboxes(self) -> list[str]:
        conn = self._ensure_connected()
        status, mailboxes = conn.list()
        if status != "OK":
            return []
        result = []
        for mb in mailboxes:
            if isinstance(mb, bytes):
                # Parse mailbox name from response
                match = re.search(rb'"([^"]+)"$', mb)
                if match:
                    result.append(match.group(1).decode("utf-8"))
        return result

    def select_mailbox(self, mailbox: str = "INBOX") -> int:
        conn = self._ensure_connected()
        status, data = conn.select(mailbox)
        if status != "OK":
            raise Exception(f"Failed to select mailbox: {mailbox}")
        return int(data[0])

    def search(
        self,
        criteria: str = "ALL",
        mailbox: str = "INBOX",
    ) -> list[bytes]:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)
        status, data = conn.search(None, criteria)
        if status != "OK":
            return []
        return data[0].split()

    def fetch_email(self, email_id: bytes, mailbox: str = "INBOX") -> Optional[Email]:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)

        # Fetch with Gmail extensions for thread ID
        status, data = conn.fetch(email_id, "(RFC822 X-GM-THRID X-GM-MSGID FLAGS)")
        if status != "OK" or not data or not data[0]:
            return None

        # Parse response
        thread_id = None
        gmail_msg_id = None
        flags = []

        for item in data:
            if isinstance(item, tuple):
                header = item[0].decode("utf-8", errors="replace") if isinstance(item[0], bytes) else str(item[0])

                # Extract X-GM-THRID
                thrid_match = re.search(r"X-GM-THRID (\d+)", header)
                if thrid_match:
                    thread_id = thrid_match.group(1)

                # Extract X-GM-MSGID
                msgid_match = re.search(r"X-GM-MSGID (\d+)", header)
                if msgid_match:
                    gmail_msg_id = msgid_match.group(1)

                # Extract FLAGS
                flags_match = re.search(r"FLAGS \(([^)]*)\)", header)
                if flags_match:
                    flags = flags_match.group(1).split()

                # Parse email content
                if len(item) > 1 and isinstance(item[1], bytes):
                    msg = email.message_from_bytes(item[1])
                    return self._parse_email(
                        msg,
                        email_id.decode("utf-8"),
                        thread_id,
                        gmail_msg_id,
                        flags,
                    )

        return None

    def fetch_emails(
        self,
        mailbox: str = "INBOX",
        criteria: str = "ALL",
        limit: int = 50,
    ) -> list[Email]:
        email_ids = self.search(criteria, mailbox)

        # Get most recent emails first
        email_ids = list(reversed(email_ids[-limit:]))

        emails = []
        for eid in email_ids:
            try:
                parsed = self.fetch_email(eid, mailbox)
                if parsed:
                    emails.append(parsed)
            except Exception as e:
                logger.error(f"Error fetching email {eid}: {e}")

        return emails

    def fetch_unread(self, mailbox: str = "INBOX", limit: int = 50) -> list[Email]:
        return self.fetch_emails(mailbox, "UNSEEN", limit)

    def _parse_email(
        self,
        msg: email.message.Message,
        email_id: str,
        thread_id: Optional[str],
        gmail_msg_id: Optional[str],
        flags: list[str],
    ) -> Email:
        # Parse addresses
        from_addr = self._parse_address(msg.get("From", ""))
        to_addrs = self._parse_address_list(msg.get("To", ""))
        cc_addrs = self._parse_address_list(msg.get("Cc", ""))

        # Parse subject
        subject = self._decode_header(msg.get("Subject", ""))

        # Parse body
        body_plain, body_html, attachments = self._parse_body(msg)

        # Parse date (ensure timezone-aware)
        date_str = msg.get("Date")
        try:
            received_at = parsedate_to_datetime(date_str) if date_str else datetime.now(timezone.utc)
            # Ensure timezone-aware
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
        except Exception:
            received_at = datetime.now(timezone.utc)

        # Parse message references
        message_id = safe_str(msg.get("Message-ID", gmail_msg_id or email_id))
        in_reply_to = safe_str(msg.get("In-Reply-To")) if msg.get("In-Reply-To") else None
        references_str = safe_str(msg.get("References", ""))
        references = references_str.split() if references_str else []

        # Determine read status from flags
        is_read = "\\Seen" in flags
        is_starred = "\\Flagged" in flags

        # Extract labels from flags
        labels = [safe_str(f) for f in flags if f.startswith("\\") and f not in ("\\Seen", "\\Flagged", "\\Recent")]

        # Create snippet from body
        snippet = None
        if body_plain:
            snippet = safe_str(body_plain[:200].replace("\n", " ").strip())

        return Email(
            id=email_id,
            account=self.account.email,
            thread_id=thread_id,
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=references,
            from_address=from_addr,
            to_addresses=to_addrs,
            cc_addresses=cc_addrs,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
            snippet=snippet,
            attachments=attachments,
            received_at=received_at,
            is_read=is_read,
            is_starred=is_starred,
            labels=labels,
        )

    def _decode_header(self, value: str) -> str:
        if not value:
            return ""
        try:
            decoded_parts = decode_header(value)
            result = []
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    result.append(part.decode(charset or "utf-8", errors="replace"))
                else:
                    result.append(str(part))
            return safe_str("".join(result))
        except Exception:
            return safe_str(value)

    def _parse_address(self, addr_str: str) -> EmailAddress:
        name, email_addr = parseaddr(self._decode_header(addr_str))
        return EmailAddress(
            email=safe_str(email_addr) or "unknown@unknown.com",
            name=safe_str(name) if name else None,
        )

    def _parse_address_list(self, addr_str: str) -> list[EmailAddress]:
        if not addr_str:
            return []
        # Split by comma, but be careful with quoted names
        addresses = []
        for addr in addr_str.split(","):
            addr = addr.strip()
            if addr:
                addresses.append(self._parse_address(addr))
        return addresses

    def _parse_body(
        self,
        msg: email.message.Message,
    ) -> tuple[Optional[str], Optional[str], list[Attachment]]:
        body_plain = None
        body_html = None
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    # Skip attachment content for now (Phase 2)
                    filename = part.get_filename() or "unnamed"
                    filename = self._decode_header(filename)
                    payload = part.get_payload(decode=True)
                    size = len(payload) if payload else 0
                    attachments.append(
                        Attachment(
                            filename=filename,
                            content_type=content_type,
                            size=size,
                        )
                    )
                elif content_type == "text/plain" and not body_plain:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body_plain = safe_str(payload.decode(charset, errors="replace"))
                elif content_type == "text/html" and not body_html:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body_html = safe_str(payload.decode(charset, errors="replace"))
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                decoded = safe_str(payload.decode(charset, errors="replace"))
                if content_type == "text/html":
                    body_html = decoded
                else:
                    body_plain = decoded

        return body_plain, body_html, attachments

    # Email actions
    def mark_read(self, email_id: str, mailbox: str = "INBOX") -> bool:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)
        status, _ = conn.store(email_id, "+FLAGS", "\\Seen")
        return status == "OK"

    def mark_unread(self, email_id: str, mailbox: str = "INBOX") -> bool:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)
        status, _ = conn.store(email_id, "-FLAGS", "\\Seen")
        return status == "OK"

    def archive(self, email_id: str, mailbox: str = "INBOX") -> bool:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)
        # Gmail: remove from inbox = archive
        status, _ = conn.store(email_id, "-X-GM-LABELS", "\\Inbox")
        return status == "OK"

    def delete(self, email_id: str, mailbox: str = "INBOX") -> bool:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)
        # Move to trash
        status, _ = conn.store(email_id, "+X-GM-LABELS", "\\Trash")
        if status == "OK":
            conn.store(email_id, "-X-GM-LABELS", "\\Inbox")
        return status == "OK"

    def star(self, email_id: str, mailbox: str = "INBOX") -> bool:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)
        status, _ = conn.store(email_id, "+FLAGS", "\\Flagged")
        return status == "OK"

    def unstar(self, email_id: str, mailbox: str = "INBOX") -> bool:
        conn = self._ensure_connected()
        self.select_mailbox(mailbox)
        status, _ = conn.store(email_id, "-FLAGS", "\\Flagged")
        return status == "OK"
