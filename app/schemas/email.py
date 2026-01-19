"""Email-related request and response schemas."""

import datetime as dt
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TimePeriod(str, Enum):
    """Available time periods for email summaries."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    WEEKEND = "weekend"


class WebhookRequest(BaseModel):
    """Gmail Pub/Sub webhook payload."""

    message: Optional[dict] = None
    subscription: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response for webhook processing."""

    message: str
    email_id: Optional[str] = None
    already_processed: bool = False


class SendSummaryRequest(BaseModel):
    """Query parameters for summary generation."""

    period: TimePeriod = Field(default=TimePeriod.MORNING)
    date: Optional[dt.date] = Field(
        default=None, description="Target date, defaults to today"
    )
    recipient: Optional[EmailStr] = Field(
        default=None, description="Override default recipient"
    )


class SendSummaryResponse(BaseModel):
    """Response for summary generation."""

    message: str
    emails_processed: int = 0
    summary_length: Optional[int] = None
    audio_generated: bool = False


class EmailData(BaseModel):
    """Internal email data structure."""

    gmail_id: str
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    email_date: Optional[dt.datetime] = None
