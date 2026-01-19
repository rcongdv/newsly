"""Tests for the SummaryGeneratorService in app.services.summary_generator."""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, AsyncMock, ANY
from zoneinfo import ZoneInfo

from app.services.summary_generator import SummaryGeneratorService
from app.schemas.email import SendSummaryRequest, TimePeriod
from app.db.models import Email


class TestSummaryGeneratorService:
    """Tests for the SummaryGeneratorService class."""

    @pytest.fixture
    def service(
        self,
        mock_settings,
        mock_email_repo,
        mock_gmail_client,
        mock_ai_service,
        mock_tts_service,
        mock_video_service,
    ):
        """Create a service instance with mocks."""
        return SummaryGeneratorService(
            settings=mock_settings,
            email_repository=mock_email_repo,
            gmail_client=mock_gmail_client,
            ai_service=mock_ai_service,
            tts_service=mock_tts_service,
            video_service=mock_video_service,
        )

    @pytest.mark.asyncio
    async def test_generate_and_send_success(
        self,
        service,
        mock_email_repo,
        mock_gmail_client,
        mock_ai_service,
        mock_tts_service,
        mock_video_service,
    ):
        """Test successful summary generation and sending."""
        # Setup mock data
        target_date = date(2023, 1, 1)
        mock_emails = [
            Email(
                sender_name="Sender 1",
                body_html="Content 1",
                email_date=datetime(2023, 1, 1, 7, 0, tzinfo=ZoneInfo("UTC")),
            ),
            Email(
                sender_name="Sender 2",
                body_html="Content 2",
                email_date=datetime(2023, 1, 1, 8, 0, tzinfo=ZoneInfo("UTC")),
            ),
        ]
        mock_email_repo.get_by_date_range.return_value = mock_emails
        mock_ai_service.summarize.return_value = "AI Generated Summary"

        request = SendSummaryRequest(period=TimePeriod.MORNING, date=target_date)
        response = await service.generate_and_send(request)

        # Verify response
        assert response.emails_processed == 2
        assert response.audio_generated is True
        assert response.video_generated is True
        assert "triggered" in response.message

        # Verify interactions
        mock_email_repo.get_by_date_range.assert_called_once()
        mock_ai_service.summarize.assert_called_once()
        mock_tts_service.text_to_speech.assert_called_once_with("AI Generated Summary")
        mock_video_service.create_video.assert_called_once()

        # Verify email sent with attachments
        mock_gmail_client.send_email.assert_called_once()
        call_args = mock_gmail_client.send_email.call_args
        assert len(call_args.kwargs["attachments"]) == 2  # Audio + Video

    @pytest.mark.asyncio
    async def test_generate_and_send_no_emails(
        self,
        service,
        mock_email_repo,
        mock_gmail_client,
        mock_ai_service,
    ):
        """Test handling when no emails are found."""
        mock_email_repo.get_by_date_range.return_value = []

        request = SendSummaryRequest(period=TimePeriod.MORNING)
        response = await service.generate_and_send(request)

        assert response.emails_processed == 0
        assert "No emails found" in response.message

        # Verify empty summary email sent
        mock_gmail_client.send_email.assert_called_once_with(
            to=ANY,
            subject=ANY,
            body_text="No news found.",
            attachments=[],
        )

        # AI service should NOT be called
        mock_ai_service.summarize.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_and_send_without_video(
        self,
        mock_settings,
        mock_email_repo,
        mock_gmail_client,
        mock_ai_service,
        mock_tts_service,
    ):
        """Test generation without video service enabled."""
        # Initialize service without video_service
        service = SummaryGeneratorService(
            settings=mock_settings,
            email_repository=mock_email_repo,
            gmail_client=mock_gmail_client,
            ai_service=mock_ai_service,
            tts_service=mock_tts_service,
            video_service=None,  # Disabled
        )

        mock_email_repo.get_by_date_range.return_value = [Email(body_html="test")]

        request = SendSummaryRequest(period=TimePeriod.MORNING)
        response = await service.generate_and_send(request)

        assert response.video_generated is False
        assert response.audio_generated is True

        # Verify only 1 attachment (Audio)
        call_args = mock_gmail_client.send_email.call_args
        assert len(call_args.kwargs["attachments"]) == 1

    @pytest.mark.asyncio
    async def test_unknown_period(self, service, mock_settings):
        """Test handling of unknown time period."""
        # Remove period from settings to simulate unknown
        mock_settings.time_frames = {}

        request = SendSummaryRequest(period=TimePeriod.MORNING)
        response = await service.generate_and_send(request)

        assert "Unknown period" in response.message
        assert response.emails_processed == 0

    @pytest.mark.asyncio
    async def test_recipient_override(
        self, service, mock_email_repo, mock_gmail_client
    ):
        """Test that recipient can be overridden in request."""
        mock_email_repo.get_by_date_range.return_value = []  # No emails needed

        request = SendSummaryRequest(
            period=TimePeriod.MORNING, recipient="custom@example.com"
        )
        await service.generate_and_send(request)

        mock_gmail_client.send_email.assert_called_once()
        assert (
            mock_gmail_client.send_email.call_args.kwargs["to"] == "custom@example.com"
        )
