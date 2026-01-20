"""Email processing endpoints."""

import logging
from datetime import date

from fastapi import APIRouter, Query, Request
from pydantic import EmailStr

from app.core.config import get_settings
from app.core.dependencies import APIKeyDep, EmailProcessorDep, SummaryGeneratorDep
from app.core.rate_limit import limiter
from app.schemas.email import (
    TimePeriod,
    WebhookRequest,
    WebhookResponse,
    SendSummaryRequest,
    SendSummaryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/new", response_model=WebhookResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
async def process_new_event(
    request: Request,
    webhook_request: WebhookRequest,
    service: EmailProcessorDep,
    _api_key: APIKeyDep,
) -> WebhookResponse:
    """
    Process incoming Gmail webhook notification.

    Requires API key authentication via X-API-Key header.
    Rate limited to prevent abuse.

    Receives notifications from Gmail Pub/Sub when new emails arrive,
    fetches the latest email, and stores it in the database.
    """
    logger.info("=== Starting process_new_event ===")
    return await service.process_webhook(webhook_request)


@router.post("/send", response_model=SendSummaryResponse)
@limiter.limit(lambda: f"{get_settings().rate_limit_per_minute}/minute")
async def send_summary(
    request: Request,
    service: SummaryGeneratorDep,
    _api_key: APIKeyDep,
    period: TimePeriod = Query(default=TimePeriod.MORNING),
    date_param: date | None = Query(default=None, alias="date"),
    recipient: EmailStr | None = Query(default=None),
) -> SendSummaryResponse:
    """
    Generate and send email summary.

    Requires API key authentication via X-API-Key header.
    Rate limited to prevent abuse.

    Queries emails for the specified period, generates an AI summary,
    creates TTS audio, and sends the summary via email.

    Args:
        period: Time period to summarize (morning or afternoon)
        date_param: Target date (defaults to today)
        recipient: Override default email recipient (must be valid email)
    """
    logger.info("=== Starting send_email ===")
    request_obj = SendSummaryRequest(
        period=period,
        date=date_param,
        recipient=recipient,
    )
    return await service.generate_and_send(request_obj)
