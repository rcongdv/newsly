"""FastAPI dependency injection setup."""

import logging
import secrets
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import get_database
from app.db.repositories.email import EmailRepository
from app.integrations.gmail.client import GmailClient, create_gmail_client
from app.integrations.ai.base import AIService
from app.integrations.ai.factory import AIFactory
from app.integrations.tts.base import TTSService
from app.integrations.tts.factory import TTSFactory
from app.integrations.video.base import VideoService
from app.integrations.video.factory import VideoFactory
from app.services.email_processor import EmailProcessorService
from app.services.summary_generator import SummaryGeneratorService


# ============ Settings Dependency ============
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ============ Authentication ============
logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def _verify_api_key(api_key: str | None, settings: Settings) -> bool:
    """Verify API key using constant-time comparison."""
    if not api_key:
        return False
    return secrets.compare_digest(api_key, settings.api_key)


def _verify_oidc_token(token: str, settings: Settings) -> bool:
    """Verify Google OIDC token from Pub/Sub push requests.

    Returns True if token is valid and from expected service account.
    """
    if not settings.pubsub_service_account_email:
        return False

    try:
        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=settings.pubsub_audience,
        )

        # Verify the token is from the expected service account
        email = claims.get("email", "")
        if email == settings.pubsub_service_account_email:
            return True

        logger.warning(
            f"OIDC token email mismatch: expected {settings.pubsub_service_account_email}, got {email}"
        )
        return False

    except Exception as e:
        logger.warning(f"OIDC token verification failed: {e}")
        return False


def verify_auth(
    api_key: str | None = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verify authentication via API key OR OIDC token.

    Accepts either:
    - X-API-Key header with valid API key
    - Authorization: Bearer <token> with valid Google OIDC token (for Pub/Sub)

    Raises HTTPException 401 if neither is valid.
    """
    # Try API key first
    if _verify_api_key(api_key, settings):
        return "api_key"

    # Try OIDC token
    if bearer and _verify_oidc_token(bearer.credentials, settings):
        return "oidc"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": "Bearer, API-Key"},
    )


APIKeyDep = Annotated[str, Depends(verify_auth)]


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


def get_ai_service(settings: SettingsDep) -> AIService:
    """
    Get AI service instance.

    Uses AIFactory to select provider based on settings.ai_provider.
    IMPORTANT: Creates new instance per request to fix concurrency bug.
    The original global singleton shared chat state between requests.
    """
    return AIFactory.create(settings)


AIServiceDep = Annotated[AIService, Depends(get_ai_service)]


def get_tts_service(settings: SettingsDep) -> TTSService:
    """Get TTS service instance.

    Uses TTSFactory to select provider based on settings.tts_provider.
    """
    return TTSFactory.create(settings)


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
