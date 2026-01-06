"""ElevenLabs TTS service implementation."""

import logging
import os

from elevenlabs.client import ElevenLabs

from app.core.config import Settings
from app.core.exceptions import TTSServiceError

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """ElevenLabs text-to-speech service supporting multiple models."""

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_ids: list[str],
        base_output_path: str,
        timeout: float = 300.0,
    ):
        self._elevenlabs = ElevenLabs(api_key=api_key, timeout=timeout)
        self._voice_id = voice_id
        self._model_ids = model_ids
        self._base_output_path = base_output_path
        self._output_paths: list[str] = []

    def _generate_output_path(self, model_id: str) -> str:
        """Generate unique output path for a model."""
        base, ext = os.path.splitext(self._base_output_path)
        return f"{base}_{model_id}{ext}"

    @property
    def output_path(self) -> str:
        """Return the primary output path (first model)."""
        if self._output_paths:
            return self._output_paths[0]
        return self._generate_output_path(self._model_ids[0])

    @property
    def output_paths(self) -> list[str]:
        """Return all output paths for all models."""
        return self._output_paths

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with all configured ElevenLabs models."""
        self._output_paths = []

        for model_id in self._model_ids:
            output_path = self._generate_output_path(model_id)
            logger.info(f"Generating TTS audio with ElevenLabs model: {model_id}")

            try:
                audio_generator = self._elevenlabs.text_to_speech.convert(
                    text=text,
                    voice_id=self._voice_id,
                    model_id=model_id,
                )
                audio_bytes = b"".join(audio_generator)

                with open(output_path, "wb") as f:
                    f.write(audio_bytes)

                self._output_paths.append(output_path)
                logger.info(f"TTS audio saved to {output_path}")

            except Exception as e:
                logger.error(f"ElevenLabs TTS error for model {model_id}: {e}")
                raise TTSServiceError(
                    f"Failed to generate TTS audio with ElevenLabs model {model_id}",
                    detail=str(e),
                ) from e


def create_elevenlabs_service(settings: Settings) -> ElevenLabsService:
    """Factory function to create ElevenLabsService from settings."""
    return ElevenLabsService(
        api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
        model_ids=settings.elevenlabs_model_id_list,
        base_output_path=settings.tts_output_path,
        timeout=settings.elevenlabs_timeout,
    )
