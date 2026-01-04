"""PyTTS service implementation."""

import logging

import pyttsx3

from app.core.config import Settings
from app.core.exceptions import TTSServiceError
from app.integrations.tts.base import BaseTTSService

logger = logging.getLogger(__name__)


class PyTTSService(BaseTTSService):
    """Local text-to-speech service using pyttsx3.

    For MP3 output, this service generates WAV first then converts using pydub.
    """

    NATIVE_FORMATS = {"wav"}

    def __init__(
        self,
        voice_rate: int,
        volume: float,
        voice_id: str,
        output_path: str,
    ):
        self._voice_rate = voice_rate
        self._volume = volume
        self._voice_id = voice_id
        self._init_format_conversion(output_path)

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with PyTTS."""
        logger.info("Generating TTS audio with PyTTS")
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self._voice_rate)
            engine.setProperty("volume", self._volume)

            voices = engine.getProperty("voices")
            voice_index = int(self._voice_id)
            if voice_index < len(voices):
                engine.setProperty("voice", voices[voice_index].id)

            wav_path = self._get_wav_output_path()
            engine.save_to_file(text, wav_path)
            engine.runAndWait()
            engine.stop()

            logger.info(f"PyTTS generated WAV: {wav_path}")
            self._convert_if_needed()
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
