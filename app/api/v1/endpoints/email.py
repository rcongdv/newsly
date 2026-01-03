"""Email processing endpoints."""

import logging
from datetime import date

from fastapi import APIRouter, Query

from app.core.dependencies import EmailProcessorDep, SummaryGeneratorDep
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
async def process_new_event(
    request: WebhookRequest,
    service: EmailProcessorDep,
) -> WebhookResponse:
    """
    Process incoming Gmail webhook notification.

    Receives notifications from Gmail Pub/Sub when new emails arrive,
    fetches the latest email, and stores it in the database.
    """
    logger.info("=== Starting process_new_event ===")
    return await service.process_webhook(request)


@router.post("/send", response_model=SendSummaryResponse)
async def send_summary(
    service: SummaryGeneratorDep,
    period: TimePeriod = Query(default=TimePeriod.MORNING),
    date_param: date | None = Query(default=None, alias="date"),
    recipient: str | None = Query(default=None),
) -> SendSummaryResponse:
    """
    Generate and send email summary.

    Queries emails for the specified period, generates an AI summary,
    creates TTS audio, and sends the summary via email.

    Args:
        period: Time period to summarize (morning or afternoon)
        date_param: Target date (defaults to today)
        recipient: Override default email recipient
    """
    logger.info("=== Starting send_email ===")
    request = SendSummaryRequest(
        period=period,
        date=date_param,
        recipient=recipient,
    )
    return await service.generate_and_send(request)
