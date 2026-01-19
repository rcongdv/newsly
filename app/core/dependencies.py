"""FastAPI dependency injection setup."""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import get_database
from app.db.repositories.email import EmailRepository
from app.integrations.gmail.client import GmailClient, create_gmail_client
from app.integrations.ai.grok import GrokService, create_grok_service
from app.integrations.tts.base import TTSService
from app.integrations.tts.factory import TTSFactory
from app.integrations.video.base import VideoService
from app.integrations.video.factory import VideoFactory
from app.services.email_processor import EmailProcessorService
from app.services.summary_generator import SummaryGeneratorService


# ============ Settings Dependency ============
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ============ Database Session Dependency ============
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for the request."""
    async with get_database().async_session() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


# ============ Repository Dependencies ============
async def get_email_repository(
    session: DBSessionDep,
) -> EmailRepository:
    """Get email repository instance."""
    return EmailRepository(session)


EmailRepoDep = Annotated[EmailRepository, Depends(get_email_repository)]


# ============ Integration Dependencies ============
def get_gmail_client(settings: SettingsDep) -> GmailClient:
    """Get Gmail client instance."""
    return create_gmail_client(settings)


GmailClientDep = Annotated[GmailClient, Depends(get_gmail_client)]


def get_ai_service(settings: SettingsDep) -> GrokService:
    """
    Get AI service instance.

    IMPORTANT: Creates new instance per request to fix concurrency bug.
    The original global singleton shared chat state between requests.
    """
    return create_grok_service(settings)


AIServiceDep = Annotated[GrokService, Depends(get_ai_service)]


def get_tts_service(settings: SettingsDep) -> TTSService:
    """Get TTS service instance based on settings."""
    return TTSFactory.create_from_settings(settings)


TTSServiceDep = Annotated[TTSService, Depends(get_tts_service)]


def get_video_service(settings: SettingsDep) -> VideoService | None:
    """Get video service instance if enabled, otherwise None."""
    return VideoFactory.create_from_settings(settings)


VideoServiceDep = Annotated[VideoService | None, Depends(get_video_service)]


# ============ Service Layer Dependencies ============
def get_email_processor_service(
    settings: SettingsDep,
    email_repo: EmailRepoDep,
    gmail_client: GmailClientDep,
) -> EmailProcessorService:
    """Get email processor service instance."""
    return EmailProcessorService(
        settings=settings,
        email_repository=email_repo,
        gmail_client=gmail_client,
    )


EmailProcessorDep = Annotated[EmailProcessorService, Depends(get_email_processor_service)]


def get_summary_generator_service(
    settings: SettingsDep,
    email_repo: EmailRepoDep,
    gmail_client: GmailClientDep,
    ai_service: AIServiceDep,
    tts_service: TTSServiceDep,
    video_service: VideoServiceDep,
) -> SummaryGeneratorService:
    """Get summary generator service instance."""
    return SummaryGeneratorService(
        settings=settings,
        email_repository=email_repo,
        gmail_client=gmail_client,
        ai_service=ai_service,
        tts_service=tts_service,
        video_service=video_service,
    )


SummaryGeneratorDep = Annotated[SummaryGeneratorService, Depends(get_summary_generator_service)]
