"""Gemini AI service with fixed concurrency - creates new request per call."""

import logging
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Gemini AI service with stateless per-request calls.

    IMPORTANT: This follows the same concurrency-safe pattern as GrokService.
    Each summarize() call is a fresh API request with no shared state,
    preventing context pollution between concurrent users.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        language: str = "en",
        system_prompt_path: Path | None = None,
    ):
        if not api_key:
            raise ValueError("Missing required GEMINI_API_KEY")

        self._api_key = api_key
        self._model = model

        # Create the client with the API key
        self._client = genai.Client(api_key=api_key)

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
        Generate summary with a fresh API request.

        CRITICAL: Each call is a stateless request to prevent context pollution
        between concurrent requests. This follows the same pattern as GrokService.
        """
        logger.info("Calling Gemini API for summarization")

        response = self._client.models.generate_content(
            model=self._model,
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=self._system_prompt,
            ),
        )

        logger.info(f"Generated summary, length: {len(response.text)} chars")
        return response.text

    def prompt(self, prompt_text: str) -> str:
        """
        Synchronous prompt method for backward compatibility.

        Note: Returns just the content string for compatibility with existing code
        that expects response.content pattern.
        """
        return self.summarize(prompt_text)


def create_gemini_service(settings: Settings) -> GeminiService:
    """Factory function to create GeminiService from settings."""
    return GeminiService(api_key=settings.gemini_api_key, model=settings.gemini_model)
