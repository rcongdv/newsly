"""Grok AI service with fixed concurrency - creates new chat per request."""

import logging
from pathlib import Path

from xai_sdk import Client
from xai_sdk.chat import user, system

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GrokService:
    """
    Grok AI service with stateless per-request chat.

    IMPORTANT: This fixes the concurrency bug from the original implementation.
    The original Grok class created self.chat once in __init__ and shared it
    across all requests, causing chat context pollution between concurrent users.

    This implementation creates a new chat instance for each summarize() call.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "grok-3-mini",
        language: str = "en",
        system_prompt_path: Path | None = None,
    ):
        if not api_key:
            raise ValueError("Missing required GROK_API_KEY")

        self._api_key = api_key
        self._model = model
        self._client = Client(api_key=api_key)

        # Load system prompt once at initialization
        prompt_path = system_prompt_path or Path(__file__).parent / "system_prompt.md"
        if prompt_path.exists():
            self._system_prompt = prompt_path.read_text().strip()
        else:
            self._system_prompt = (
                "You are a helpful assistant that summarizes news content."
            )
            logger.warning(f"System prompt not found at {prompt_path}, using default")

        if language == "ch":
            self._system_prompt += "\nRespond in Mandarin Chinese."

    def summarize(self, content: str) -> str:
        """
        Generate summary with a fresh chat context per request.

        CRITICAL: Creates new chat instance to prevent state pollution
        between concurrent requests. This is the key fix for the concurrency bug.
        """
        logger.info("Creating new chat instance for summarization")

        # NEW CHAT PER REQUEST - this is the fix
        chat = self._client.chat.create(
            model=self._model,
            messages=[system(self._system_prompt)],
        )

        chat.append(user(content))
        response = chat.sample()

        logger.info(f"Generated summary, length: {len(response.content)} chars")
        return response.content

    def prompt(self, prompt_text: str) -> str:
        """
        Synchronous prompt method for backward compatibility.

        Note: Returns just the content string for compatibility with existing code
        that expects response.content pattern.
        """
        return self.summarize(prompt_text)


def create_grok_service(settings: Settings) -> GrokService:
    """Factory function to create GrokService from settings."""
    return GrokService(api_key=settings.grok_api_key, model=settings.grok_model)
