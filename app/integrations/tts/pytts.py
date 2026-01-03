"""PyTTS service implementation."""

import logging

import pyttsx3

from app.core.config import Settings
from app.core.exceptions import TTSServiceError

logger = logging.getLogger(__name__)


class PyTTSService:
    """Local text-to-speech service using pyttsx3."""

    def __init__(
        self,
        voice_rate: int,
        volume: float,
        voice_id: str,
        output_path: str,
    ):
        self._output_path = output_path
        self._voice_rate = voice_rate
        self._volume = volume
        self._voice_id = voice_id

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with PyTTS."""
        logger.info("Generating TTS audio with PyTTS")
        try:
            # Initialize engine for each request to avoid state issues
            engine = pyttsx3.init()
            engine.setProperty("rate", self._voice_rate)
            engine.setProperty("volume", self._volume)

            voices = engine.getProperty("voices")
            voice_index = int(self._voice_id)
            if voice_index < len(voices):
                engine.setProperty("voice", voices[voice_index].id)

            engine.save_to_file(text, self._output_path)
            engine.runAndWait()
            engine.stop()

            logger.info(f"TTS audio saved to {self._output_path}")
        except Exception as e:
            logger.error(f"PyTTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with PyTTS",
                detail=str(e),
            ) from e


def create_pytts_service(settings: Settings) -> PyTTSService:
    """Factory function to create PyTTSService from settings."""
    return PyTTSService(
        voice_rate=settings.pytts_voice_rate,
        volume=settings.pytts_volume,
        voice_id=settings.pytts_voice_id,
        output_path=settings.tts_output_path,
    )
