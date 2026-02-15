import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from .config import GmailAccountConfig
from .models import SendEmailRequest

logger = logging.getLogger(__name__)


class SMTPClient:
    def __init__(self, account: GmailAccountConfig):
        self.account = account
        self._connection: Optional[smtplib.SMTP_SSL] = None

    def connect(self) -> None:
        if self._connection:
            return
        logger.info(f"Connecting to SMTP server for {self.account.email}")
        self._connection = smtplib.SMTP_SSL(
            self.account.smtp_server,
            self.account.smtp_port,
        )
        self._connection.login(self.account.email, self.account.app_password)
        logger.info(f"Connected to SMTP server for {self.account.email}")

    def disconnect(self) -> None:
        if self._connection:
            try:
                self._connection.quit()
            except Exception:
                pass
            self._connection = None
            logger.info(f"Disconnected from SMTP for {self.account.email}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _ensure_connected(self) -> smtplib.SMTP_SSL:
        if not self._connection:
            self.connect()
        return self._connection  # type: ignore

    def send(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        html: bool = False,
        reply_to_message_id: Optional[str] = None,
        references: Optional[list[str]] = None,
    ) -> bool:
        conn = self._ensure_connected()

        # Create message
        if html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "html"))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, "plain"))

        msg["Subject"] = subject
        msg["From"] = self.account.email
        msg["To"] = ", ".join(to)

        if cc:
            msg["Cc"] = ", ".join(cc)

        # Set reply headers for threading
        if reply_to_message_id:
            msg["In-Reply-To"] = reply_to_message_id
            if references:
                msg["References"] = " ".join(references + [reply_to_message_id])
            else:
                msg["References"] = reply_to_message_id

        # Build recipient list
        recipients = list(to)
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)

        try:
            conn.sendmail(self.account.email, recipients, msg.as_string())
            logger.info(f"Email sent to {recipients}")
            return True
        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_email(self, request: SendEmailRequest) -> bool:
        return self.send(
            to=list(request.to),
            subject=request.subject,
            body=request.body,
            cc=list(request.cc) if request.cc else None,
            bcc=list(request.bcc) if request.bcc else None,
            html=request.html,
            reply_to_message_id=request.reply_to_message_id,
        )

    def reply(
        self,
        original_message_id: str,
        original_references: list[str],
        to: list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        html: bool = False,
    ) -> bool:
        # Ensure subject has Re: prefix
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        return self.send(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            html=html,
            reply_to_message_id=original_message_id,
            references=original_references,
        )
