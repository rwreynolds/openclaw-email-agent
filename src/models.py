from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EmailCategory(str, Enum):
    WORK = "Work"
    PERSONAL = "Personal"
    NEWSLETTERS = "Newsletters"
    SPAM = "Spam"
    NOTIFICATIONS = "Notifications"
    UNKNOWN = "Unknown"


class EmailAddress(BaseModel):
    email: EmailStr
    name: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


class Attachment(BaseModel):
    filename: str
    content_type: str
    size: int


class Email(BaseModel):
    id: str
    account: EmailStr
    thread_id: Optional[str] = None
    message_id: str
    in_reply_to: Optional[str] = None
    references: list[str] = Field(default_factory=list)

    from_address: EmailAddress
    to_addresses: list[EmailAddress] = Field(default_factory=list)
    cc_addresses: list[EmailAddress] = Field(default_factory=list)
    bcc_addresses: list[EmailAddress] = Field(default_factory=list)

    subject: str
    body_plain: Optional[str] = None
    body_html: Optional[str] = None
    snippet: Optional[str] = None

    attachments: list[Attachment] = Field(default_factory=list)

    received_at: datetime
    is_read: bool = False
    is_starred: bool = False
    labels: list[str] = Field(default_factory=list)

    # AI-generated fields
    summary: Optional[str] = None
    classification: Optional[EmailCategory] = None


class EmailThread(BaseModel):
    id: str
    account: EmailStr
    subject: str
    participants: list[EmailAddress] = Field(default_factory=list)
    email_count: int = 0
    emails: list[Email] = Field(default_factory=list)
    latest_email_at: datetime
    has_unread: bool = False


class Account(BaseModel):
    id: str
    email: EmailStr
    is_connected: bool = False
    last_sync_at: Optional[datetime] = None
    email_count: Optional[int] = None


class SendEmailRequest(BaseModel):
    account: EmailStr
    to: list[EmailStr]
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    subject: str
    body: str
    html: bool = False
    reply_to_message_id: Optional[str] = None


class EmailListResponse(BaseModel):
    emails: list[Email]
    total: int
    page: int = 1
    page_size: int = 50


class ThreadListResponse(BaseModel):
    threads: list[EmailThread]
    total: int
    page: int = 1
    page_size: int = 50


class ClassificationResult(BaseModel):
    email_id: str
    category: EmailCategory
    confidence: float = 0.0


class SummaryResult(BaseModel):
    email_id: str
    summary: str


class WebhookPayload(BaseModel):
    event: str = "new_email"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    account: EmailStr
    emails: list[dict]
