"""Summary generator service for creating and sending email summaries."""

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.db.repositories.email import EmailRepository
from app.integrations.gmail.client import GmailClient
from app.integrations.ai.grok import GrokService
from app.integrations.tts.base import TTSService
from app.schemas.email import SendSummaryRequest, SendSummaryResponse

logger = logging.getLogger(__name__)


class SummaryGeneratorService:
    """Service for generating and sending email summaries."""

    def __init__(
        self,
        settings: Settings,
        email_repository: EmailRepository,
        gmail_client: GmailClient,
        ai_service: GrokService,
        tts_service: TTSService,
    ):
        self._settings = settings
        self._email_repo = email_repository
        self._gmail_client = gmail_client
        self._ai_service = ai_service
        self._tts_service = tts_service

    async def generate_and_send(
        self, request: SendSummaryRequest
    ) -> SendSummaryResponse:
        """
        Generate summary from emails and send it.

        Queries emails for the specified period, generates an AI summary,
        creates TTS audio, and sends the summary via email.
        """
        target_date = request.date or date.today()
        period = request.period.value

        logger.info(f"Generating summary for {target_date} {period}")

        # Get time range from settings
        time_frame = self._settings.time_frames.get(period)
        if not time_frame:
            logger.error(f"Unknown period: {period}")
            return SendSummaryResponse(
                message=f"Unknown period: {period}",
                emails_processed=0,
            )

        tz = ZoneInfo(self._settings.timezone)
        start_dt, end_dt = self._build_date_range(target_date, time_frame, tz)

        logger.info(f"Querying emails from {start_dt} to {end_dt}")
        logger.info(f"Allowed domains: {self._settings.email_domain_whitelist_list}")

        # Query emails
        emails = await self._email_repo.get_by_date_range(
            start_date=start_dt,
            end_date=end_dt,
            allowed_domains=self._settings.email_domain_whitelist_list,
        )

        logger.info(f"Found {len(emails)} emails in date range")

        # Determine recipient
        recipient = request.recipient or self._settings.default_recipient
        subject = f"Newsly Summary for {target_date} {period.capitalize()}"

        if not emails:
            logger.info("No emails found, sending empty summary")
            self._gmail_client.send_email(
                to=recipient,
                subject=subject,
                body_text="No news found.",
                attachments=[],
            )
            return SendSummaryResponse(
                message="No emails found, sent empty summary",
                emails_processed=0,
            )

        # Generate AI summary
        logger.info(f"Processing {len(emails)} emails for AI summary")
        emails_text = "\n\nNEXT EMAIL:\n\n".join(
            email.body_html for email in emails if email.body_html
        )

        logger.info("Calling AI service for summary...")
        summary = self._ai_service.summarize(emails_text)

        # Add sources
        sender_names = [email.sender_name for email in emails if email.sender_name]
        sources_text = "\n\nSources: " + ", ".join(sender_names)
        body = summary + sources_text

        logger.info(f"AI summary generated, length: {len(body)} chars")

        # Generate TTS
        logger.info("Generating TTS audio...")
        self._tts_service.text_to_speech(summary)
        attachments = self._tts_service.output_paths
        logger.info(f"TTS complete, attachments: {attachments}")

        # Send email
        logger.info(f"Sending summary email to {recipient}...")
        self._gmail_client.send_email(
            to=recipient,
            subject=subject,
            body_text=body,
            attachments=attachments,
        )
        logger.info("Summary email sent successfully")

        return SendSummaryResponse(
            message="Email sending triggered",
            emails_processed=len(emails),
            summary_length=len(summary),
            audio_generated=True,
        )

    def _build_date_range(
        self,
        target_date: date,
        time_frame: tuple[str, str],
        tz: ZoneInfo,
    ) -> tuple[datetime, datetime]:
        """Build datetime range from date and time frame."""
        time_format = self._settings.time_format

        start_dt = datetime.combine(
            target_date,
            datetime.strptime(time_frame[0], time_format).time(),
            tzinfo=tz,
        )
        end_dt = datetime.combine(
            target_date,
            datetime.strptime(time_frame[1], time_format).time(),
            tzinfo=tz,
        )
        return start_dt, end_dt
