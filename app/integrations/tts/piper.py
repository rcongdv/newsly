"""Piper TTS service implementation.

Piper is a fast, local neural text-to-speech system optimized for
low-resource environments like Raspberry Pi.
"""

import logging
import wave

from app.core.config import Settings
from app.core.exceptions import TTSServiceError
from app.integrations.tts.base import BaseTTSService

logger = logging.getLogger(__name__)


class PiperService(BaseTTSService):
    """Piper text-to-speech service.

    Uses the piper-tts Python library for speech synthesis.
    Outputs WAV natively, converts to other formats via pydub.
    """

    NATIVE_FORMATS = {"wav"}

    def __init__(
        self,
        model_path: str,
        output_path: str,
        speaker_id: int | None = None,
        length_scale: float = 1.0,
        sentence_silence: float = 0.2,
    ):
        self._model_path = model_path
        self._speaker_id = speaker_id
        self._length_scale = length_scale
        self._sentence_silence = sentence_silence
        self._voice = None  # Lazy initialization
        self._init_format_conversion(output_path)

    def _get_voice(self):
        """Lazy initialization of Piper voice."""
        if self._voice is None:
            try:
                from piper import PiperVoice
            except ImportError:
                raise TTSServiceError(
                    "piper-tts library not installed",
                    detail="Install with: pip install piper-tts",
                )

            logger.info(f"Loading Piper model: {self._model_path}")
            self._voice = PiperVoice.load(self._model_path)
            logger.info("Piper model loaded")

        return self._voice

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with Piper."""
        logger.info("Generating TTS audio with Piper")
        try:
            voice = self._get_voice()
            wav_path = self._get_wav_output_path()

            # Synthesize audio using synthesize_wav which handles WAV format
            with wave.open(wav_path, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)

            logger.info(f"Piper generated WAV: {wav_path}")
            self._convert_if_needed()
            logger.info(f"TTS audio saved to {self._output_path}")

        except TTSServiceError:
            raise
        except Exception as e:
            logger.error(f"Piper TTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with Piper",
                detail=str(e),
            ) from e


def create_piper_service(settings: Settings) -> PiperService:
    """Factory function to create PiperService from settings."""
    return PiperService(
        model_path=settings.piper_model_path,
        output_path=settings.tts_output_path,
        speaker_id=settings.piper_speaker_id,
        length_scale=settings.piper_length_scale,
        sentence_silence=settings.piper_sentence_silence,
    )
