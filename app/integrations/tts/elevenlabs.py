"""ElevenLabs TTS service implementation."""

import logging

from elevenlabs.client import ElevenLabs

from app.core.config import Settings
from app.core.exceptions import TTSServiceError

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """ElevenLabs text-to-speech service."""

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str,
        output_path: str,
    ):
        self._elevenlabs = ElevenLabs(api_key=api_key)
        self._voice_id = voice_id
        self._model_id = model_id
        self._output_path = output_path

    @property
    def output_path(self) -> str:
        """Return the output path where audio will be saved."""
        return self._output_path

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with ElevenLabs."""
        logger.info("Generating TTS audio with ElevenLabs")
        try:
            audio_generator = self._elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=self._voice_id,
                model_id=self._model_id,
            )
            audio_bytes = b"".join(audio_generator)
            with open(self._output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"TTS audio saved to {self._output_path}")
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with ElevenLabs",
                detail=str(e),
            ) from e


def create_elevenlabs_service(settings: Settings) -> ElevenLabsService:
    """Factory function to create ElevenLabsService from settings."""
    return ElevenLabsService(
        api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
        model_id=settings.elevenlabs_model_id,
        output_path=settings.tts_output_path,
    )
