"""FastAPI dependency injection setup."""

import secrets
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import get_database
from app.db.repositories.email import EmailRepository
from app.integrations.gmail.client import GmailClient, create_gmail_client
from app.integrations.ai.grok import GrokService, create_grok_service
from app.integrations.tts.elevenlabs import ElevenLabsService, create_elevenlabs_service
from app.integrations.video.base import VideoService
from app.integrations.video.factory import VideoFactory
from app.services.email_processor import EmailProcessorService
from app.services.summary_generator import SummaryGeneratorService


# ============ Settings Dependency ============
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ============ API Key Authentication ============
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verify the API key from request header.

    Raises HTTPException 401 if API key is missing or invalid.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API key"},
        )

    return api_key


APIKeyDep = Annotated[str, Depends(verify_api_key)]


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


def get_tts_service(settings: SettingsDep) -> ElevenLabsService:
    """Get TTS service instance."""
    return create_elevenlabs_service(settings)


TTSServiceDep = Annotated[ElevenLabsService, Depends(get_tts_service)]


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


EmailProcessorDep = Annotated[
    EmailProcessorService, Depends(get_email_processor_service)
]


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


SummaryGeneratorDep = Annotated[
    SummaryGeneratorService, Depends(get_summary_generator_service)
]
