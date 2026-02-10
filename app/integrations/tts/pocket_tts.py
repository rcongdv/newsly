"""Pocket TTS service implementation (local/CPU-based TTS by Kyutai)."""

import logging
import os
import tempfile

import scipy.io.wavfile
from pocket_tts import TTSModel
from pydub import AudioSegment

from app.core.config import Settings
from app.core.exceptions import TTSServiceError
from app.integrations.tts.base import WordTiming

logger = logging.getLogger(__name__)


class PocketTTSService:
    """Pocket TTS text-to-speech service (local CPU-based, no API key required).

    Pocket TTS generates WAV natively. The output is then converted to MP3
    to keep file sizes small enough for email attachments (WAV is uncompressed
    and would exceed Gmail's size limits for anything beyond short clips).

    Note: Word-level timing is not supported by Pocket TTS.
    The word_timings property always returns an empty list.
    """

    def __init__(self, voice: str, output_path: str):
        self._voice = voice
        self._output_path = output_path
        self._word_timings: list[WordTiming] = []

        # Load model and voice state once (these are slow operations)
        logger.info("Loading Pocket TTS model...")
        self._model = TTSModel.load_model()
        logger.info(f"Loading Pocket TTS voice state for: {voice}")
        self._voice_state = self._model.get_state_for_audio_prompt(voice)
        logger.info("Pocket TTS model and voice state loaded successfully")

    @property
    def output_path(self) -> str:
        """Return the output path where audio will be saved."""
        return self._output_path

    @property
    def word_timings(self) -> list[WordTiming]:
        """Return word timing data (not supported by Pocket TTS)."""
        return self._word_timings

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with Pocket TTS.

        Generates WAV internally, then converts to MP3 for the final output
        to keep file sizes manageable for email delivery.
        """
        logger.info("Generating TTS audio with Pocket TTS")
        try:
            audio = self._model.generate_audio(self._voice_state, text)

            # Write WAV to a temp file, then convert to MP3
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_wav_path = tmp.name
                scipy.io.wavfile.write(
                    tmp_wav_path,
                    self._model.sample_rate,
                    audio.numpy(),
                )

            try:
                sound = AudioSegment.from_wav(tmp_wav_path)
                sound.export(self._output_path, format="mp3")
                logger.info(f"TTS audio saved to {self._output_path}")
            finally:
                os.remove(tmp_wav_path)

        except Exception as e:
            logger.error(f"Pocket TTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with Pocket TTS",
                detail=str(e),
            ) from e


def create_pocket_tts_service(settings: Settings) -> PocketTTSService:
    """Factory function to create PocketTTSService from settings."""
    return PocketTTSService(
        voice=settings.pocket_tts_voice,
        output_path=settings.tts_output_path,
    )
