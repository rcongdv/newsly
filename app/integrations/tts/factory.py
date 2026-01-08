"""TTS service factory for provider selection."""

from typing import Literal

from app.core.config import Settings
from app.integrations.tts.base import TTSService
from app.integrations.tts.elevenlabs import create_elevenlabs_service
from app.integrations.tts.pytts import create_pytts_service
from app.integrations.tts.google_tts import create_google_tts_service


class TTSFactory:
    """Factory for creating TTS service instances."""

    @staticmethod
    def create(
        provider: Literal["pytts", "elevenlabs", "google"],
        settings: Settings,
    ) -> TTSService:
        """
        Create a TTS service based on provider name.

        Args:
            provider: The TTS provider to use
            settings: Application settings

        Returns:
            A TTSService implementation
        """
        match provider:
            case "elevenlabs":
                return create_elevenlabs_service(settings)
            case "google":
                return create_google_tts_service(settings)
            case _:
                return create_pytts_service(settings)

    @staticmethod
    def create_from_settings(settings: Settings) -> TTSService:
        """Create TTS service using provider from settings."""
        return TTSFactory.create(settings.tts_provider, settings)
