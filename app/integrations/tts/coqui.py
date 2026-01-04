"""Coqui TTS service implementation.

Coqui TTS is an open-source deep learning toolkit for Text-to-Speech.
Supports multiple models including XTTS for voice cloning.
"""

import logging

from app.core.config import Settings
from app.core.exceptions import TTSServiceError
from app.integrations.tts.base import BaseTTSService

logger = logging.getLogger(__name__)


class CoquiService(BaseTTSService):
    """Coqui text-to-speech service.

    Uses the TTS library for neural speech synthesis.
    Supports various models including XTTS-v2 for voice cloning.
    """

    NATIVE_FORMATS = {"wav"}

    def __init__(
        self,
        model_name: str,
        output_path: str,
        speaker_wav: str | None = None,
        language: str = "en",
        gpu: bool = False,
    ):
        self._model_name = model_name
        self._speaker_wav = speaker_wav
        self._language = language
        self._gpu = gpu
        self._tts = None  # Lazy initialization
        self._init_format_conversion(output_path)

    def _get_tts(self):
        """Lazy initialization of TTS model."""
        if self._tts is None:
            try:
                from TTS.api import TTS
            except ImportError:
                raise TTSServiceError(
                    "TTS library not installed",
                    detail="Install with: pip install TTS",
                )

            logger.info(f"Loading Coqui TTS model: {self._model_name}")
            self._tts = TTS(model_name=self._model_name, gpu=self._gpu)
            logger.info("Coqui TTS model loaded")

        return self._tts

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with Coqui TTS."""
        logger.info("Generating TTS audio with Coqui TTS")
        try:
            tts = self._get_tts()
            wav_path = self._get_wav_output_path()

            if self._speaker_wav and hasattr(tts, "tts_with_vc"):
                tts.tts_to_file(
                    text=text,
                    file_path=wav_path,
                    speaker_wav=self._speaker_wav,
                    language=self._language,
                )
            elif self._is_multispeaker_model():
                tts.tts_to_file(
                    text=text,
                    file_path=wav_path,
                    speaker_wav=self._speaker_wav,
                    language=self._language,
                )
            else:
                tts.tts_to_file(
                    text=text,
                    file_path=wav_path,
                )

            logger.info(f"Coqui TTS generated WAV: {wav_path}")
            self._convert_if_needed()
            logger.info(f"TTS audio saved to {self._output_path}")

        except Exception as e:
            logger.error(f"Coqui TTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with Coqui TTS",
                detail=str(e),
            ) from e

    def _is_multispeaker_model(self) -> bool:
        """Check if the loaded model supports multiple speakers."""
        tts = self._get_tts()
        return hasattr(tts, "speakers") and tts.speakers is not None


def create_coqui_service(settings: Settings) -> CoquiService:
    """Factory function to create CoquiService from settings."""
    return CoquiService(
        model_name=settings.coqui_model_name,
        output_path=settings.tts_output_path,
        speaker_wav=settings.coqui_speaker_wav,
        language=settings.tts_language,
        gpu=settings.coqui_use_gpu,
    )
