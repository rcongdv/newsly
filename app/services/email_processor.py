"""Email processor service for handling incoming emails."""

import logging

from app.core.config import Settings
from app.db.repositories.email import EmailRepository
from app.integrations.gmail.client import GmailClient
from app.schemas.email import WebhookRequest, WebhookResponse

logger = logging.getLogger(__name__)


class EmailProcessorService:
    """Service for processing incoming Gmail webhooks and storing emails."""

    def __init__(
        self,
        settings: Settings,
        email_repository: EmailRepository,
        gmail_client: GmailClient,
    ):
        self._settings = settings
        self._email_repo = email_repository
        self._gmail_client = gmail_client

    async def process_webhook(self, request: WebhookRequest) -> WebhookResponse:
        """
        Process Gmail webhook notification.

        Fetches the latest email, checks for duplicates, and stores new emails.
        """
        logger.info("Processing Gmail webhook notification")
        logger.info(f"Received webhook data: {request.model_dump()}")

        # Fetch latest email from Gmail
        latest_email = self._gmail_client.fetch_latest_email()

        if not latest_email or not latest_email.gmail_id:
            logger.info("No email found to process")
            return WebhookResponse(message="No email to process")

        # Check if email already exists
        existing = await self._email_repo.get_by_gmail_id(latest_email.gmail_id)
        if existing:
            logger.info(f"Email already exists in DB: {latest_email.gmail_id}")
            return WebhookResponse(
                message="Email already processed",
                email_id=latest_email.gmail_id,
                already_processed=True,
            )

        # Save new email to database
        logger.info(
            f"Saving new email: subject='{latest_email.subject}', "
            f"sender='{latest_email.sender_email}'"
        )

        await self._email_repo.create(
            gmail_id=latest_email.gmail_id,
            sender_name=latest_email.sender_name,
            sender_email=latest_email.sender_email,
            subject=latest_email.subject,
            body_html=latest_email.body_html,
            body_text=latest_email.body_text,
            email_date=latest_email.email_date,
        )

        logger.info(f"Email saved successfully: {latest_email.gmail_id}")
        return WebhookResponse(
            message="New event received and processed",
            email_id=latest_email.gmail_id,
        )
