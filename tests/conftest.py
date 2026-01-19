import os
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from typing import AsyncGenerator

# Set mock environment variables for testing before importing app
# This prevents Pydantic validation errors when importing app.main
os.environ.update(
    {
        "GOOGLE_AUTH_CLIENT_ID": "test-client-id",
        "GOOGLE_AUTH_CLIENT_SECRET": "test-client-secret",
        "GOOGLE_AUTH_REFRESH_TOKEN": "test-refresh-token",
        "GMAIL_PUBSUB_TOPIC_NAME": "projects/test/topics/test-topic",
        "GROK_API_KEY": "test-grok-key",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "ELEVENLABS_API_KEY": "test-elevenlabs-key",
        "VIDEO_ENABLED": "true",
        "VIDEO_WIDTH": "1080",
        "VIDEO_HEIGHT": "1080",
        "SUBTITLE_FONT_SIZE": "48",
        "SUBTITLE_MAX_CHARS_PER_LINE": "60",
        "DB_POOL_SIZE": "5",
        "DB_MAX_OVERFLOW": "10",
        "DB_POOL_TIMEOUT": "30",
    }
)

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings, get_settings
from app.db.repositories.email import EmailRepository
from app.integrations.gmail.client import GmailClient
from app.integrations.ai.grok import GrokService
from app.integrations.tts.base import TTSService
from app.integrations.video.base import VideoService
from app.core.dependencies import (
    get_db_session,
    get_email_repository,
    get_gmail_client,
    get_ai_service,
    get_tts_service,
    get_video_service,
)


# ============ Settings Fixture ============
@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings with test values."""
    return Settings(
        app_name="Newsly Test",
        database_url="postgresql+asyncpg://user:pass@localhost/testdb",
        google_auth_client_id="test-client-id",
        google_auth_client_secret="test-secret",
        google_auth_refresh_token="test-refresh-token",
        gmail_pubsub_topic_name="projects/test/topics/gmail",
        grok_api_key="test-grok-key",
        # Use simple time frames for easy testing
        time_frames={
            "morning": ("06:00:00", "09:00:00"),
            "afternoon": ("12:00:00", "15:00:00"),
            "weekend": ("10:00:00", "12:00:00"),
        },
        email_whitelist="example.com",
    )


# ============ Database Fixtures ============
@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result
    return session


@pytest.fixture
def mock_email_repo(mock_db_session) -> AsyncMock:
    """Create a mock email repository."""
    repo = AsyncMock(spec=EmailRepository)
    repo.session = mock_db_session
    repo.get_by_date_range.return_value = []
    repo.create_if_not_exists.return_value = (None, False)
    return repo


# ============ Service Fixtures ============
@pytest.fixture
def mock_gmail_client() -> MagicMock:
    """Create a mock Gmail client."""
    client = MagicMock(spec=GmailClient)
    return client


@pytest.fixture
def mock_ai_service() -> MagicMock:
    """Create a mock AI service."""
    service = MagicMock(spec=GrokService)
    service.summarize.return_value = "Test Summary"
    return service


@pytest.fixture
def mock_tts_service() -> MagicMock:
    """Create a mock TTS service."""
    service = MagicMock(spec=TTSService)
    service.output_path = "output.mp3"
    return service


@pytest.fixture
def mock_video_service() -> MagicMock:
    """Create a mock Video service."""
    service = MagicMock(spec=VideoService)
    service.output_path = "output.mp4"
    return service


# ============ FastAPI Test Client ============
@pytest.fixture
def client(
    mock_settings,
    mock_db_session,
    mock_email_repo,
    mock_gmail_client,
    mock_ai_service,
    mock_tts_service,
    mock_video_service,
) -> TestClient:
    """Create a TestClient with overridden dependencies."""

    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: mock_settings
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_email_repository] = lambda: mock_email_repo
    app.dependency_overrides[get_gmail_client] = lambda: mock_gmail_client
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service
    app.dependency_overrides[get_tts_service] = lambda: mock_tts_service
    app.dependency_overrides[get_video_service] = lambda: mock_video_service

    # Mock the database initialization in lifespan
    from unittest.mock import patch

    mock_db = MagicMock()
    mock_db.init_db = AsyncMock()

    # We need to patch where get_database is used in main.py, or patch the get_database function itself
    with patch("app.main.get_database", return_value=mock_db):
        # We also need to patch create_gmail_client because lifespan calls it
        with patch("app.main.create_gmail_client", return_value=mock_gmail_client):
            with TestClient(app) as test_client:
                yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()
