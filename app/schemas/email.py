"""Email-related request and response schemas."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class TimePeriod(str, Enum):
    """Available time periods for email summaries."""

    MORNING = "morning"
    AFTERNOON = "afternoon"


class WebhookRequest(BaseModel):
    """Gmail Pub/Sub webhook payload."""

    message: dict | None = None
    subscription: str | None = None


class WebhookResponse(BaseModel):
    """Response for webhook processing."""

    message: str
    email_id: str | None = None
    already_processed: bool = False


class SendSummaryRequest(BaseModel):
    """Query parameters for summary generation."""

    period: TimePeriod = Field(default=TimePeriod.MORNING)
    date: date | None = Field(
        default=None, description="Target date, defaults to today"
    )
    recipient: EmailStr | None = Field(
        default=None, description="Override default recipient"
    )


class SendSummaryResponse(BaseModel):
    """Response for summary generation."""

    message: str
    emails_processed: int = 0
    summary_length: int | None = None
    audio_generated: bool = False


class EmailData(BaseModel):
    """Internal email data structure."""

    gmail_id: str
    sender_name: str | None = None
    sender_email: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    email_date: datetime | None = None
