"""Factory for AI provider selection."""

import logging

from app.core.config import Settings
from app.integrations.ai.base import AIService
from app.integrations.ai.grok import GrokService, create_grok_service
from app.integrations.ai.gemini import GeminiService, create_gemini_service

logger = logging.getLogger(__name__)


class AIFactory:
    """Factory for creating AI service instances based on configuration."""

    @staticmethod
    def create(settings: Settings) -> AIService:
        """
        Create an AI service instance based on settings.

        Args:
            settings: Application settings containing ai_provider configuration

        Returns:
            AIService instance (GrokService or GeminiService)

        Raises:
            ValueError: If unknown provider is specified
        """
        provider = settings.ai_provider.lower()
        logger.info(f"Creating AI service for provider: {provider}")

        if provider == "grok":
            return create_grok_service(settings)
        elif provider == "gemini":
            return create_gemini_service(settings)
        else:
            raise ValueError(
                f"Unknown AI provider: {provider}. Supported providers: grok, gemini"
            )
