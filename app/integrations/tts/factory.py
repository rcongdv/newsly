"""Factory for TTS provider selection."""

import logging

from app.core.config import Settings
from app.integrations.tts.base import TTSService
from app.integrations.tts.elevenlabs import ElevenLabsService, create_elevenlabs_service
from app.integrations.tts.pocket_tts import PocketTTSService, create_pocket_tts_service

logger = logging.getLogger(__name__)


class TTSFactory:
    """Factory for creating TTS service instances based on configuration."""

    @staticmethod
    def create(settings: Settings) -> TTSService:
        """
        Create a TTS service instance based on settings.

        Args:
            settings: Application settings containing tts_provider configuration

        Returns:
            TTSService instance (ElevenLabsService or PocketTTSService)

        Raises:
            ValueError: If unknown provider is specified
        """
        provider = settings.tts_provider.lower()
        logger.info(f"Creating TTS service for provider: {provider}")

        if provider == "elevenlabs":
            return create_elevenlabs_service(settings)
        elif provider == "pocket_tts":
            return create_pocket_tts_service(settings)
        else:
            raise ValueError(
                f"Unknown TTS provider: {provider}. "
                f"Supported providers: elevenlabs, pocket_tts"
            )
