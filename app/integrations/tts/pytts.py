"""PyTTS service implementation."""

import logging
import os

import pyttsx3
from pydub import AudioSegment

from app.core.config import Settings
from app.core.exceptions import TTSServiceError

logger = logging.getLogger(__name__)


class PyTTSService:
    """Local text-to-speech service using pyttsx3.

    For MP3 output, this service generates WAV first then converts using pydub.
    """

    # pyttsx3 only supports WAV format natively
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
        self._output_path = output_path

        # Check if conversion is needed
        base, ext = os.path.splitext(output_path)
        self._target_format = ext.lower().lstrip(".")
        self._needs_conversion = self._target_format not in self.NATIVE_FORMATS

        if self._needs_conversion:
            self._temp_wav_path = f"{base}_temp.wav"
        else:
            self._temp_wav_path = None

    @property
    def output_path(self) -> str:
        """Return the output path where audio will be saved."""
        return self._output_path

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

            # Generate to temp WAV if conversion needed, otherwise direct to output
            wav_path = self._temp_wav_path if self._needs_conversion else self._output_path

            engine.save_to_file(text, wav_path)
            engine.runAndWait()
            engine.stop()

            logger.info(f"PyTTS generated WAV: {wav_path}")

            # Convert to target format if needed
            if self._needs_conversion:
                self._convert_to_target_format(wav_path)

            logger.info(f"TTS audio saved to {self._output_path}")
        except Exception as e:
            logger.error(f"PyTTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with PyTTS",
                detail=str(e),
            ) from e

    def _convert_to_target_format(self, temp_path: str) -> None:
        """Convert temp WAV file to target format (e.g., MP3)."""
        try:
            logger.info(f"Converting {temp_path} to {self._target_format}")

            audio = AudioSegment.from_wav(temp_path)
            audio.export(self._output_path, format=self._target_format)

            # Clean up temp file
            os.remove(temp_path)
            logger.info(f"Converted to {self._output_path}, removed temp file")
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            raise TTSServiceError(
                f"Failed to convert audio to {self._target_format}",
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
