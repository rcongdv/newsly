"""Base class and protocol for TTS services."""

import logging
import os
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from pydub import AudioSegment

from app.core.exceptions import TTSServiceError

logger = logging.getLogger(__name__)


@runtime_checkable
class TTSService(Protocol):
    """Protocol for text-to-speech services."""

    @property
    def output_path(self) -> str:
        """Return the actual output path where audio will be saved."""
        ...

    def text_to_speech(self, text: str) -> None:
        """Convert text to speech and save to file."""
        ...


class BaseTTSService(ABC):
    """Base class for TTS services with common format conversion logic.

    Subclasses should:
    1. Define NATIVE_FORMATS class variable with supported formats
    2. Call _init_format_conversion(output_path) in __init__
    3. Use _get_wav_output_path() to get the path for WAV generation
    4. Call _convert_if_needed() after generating the WAV file
    """

    NATIVE_FORMATS: set[str] = {"wav"}

    def _init_format_conversion(self, output_path: str) -> None:
        """Initialize format conversion settings based on output path.

        Args:
            output_path: The desired output file path (e.g., "output.mp3")
        """
        self._output_path = output_path

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

    def _get_wav_output_path(self) -> str:
        """Get the path to write WAV output to.

        Returns temp path if conversion is needed, otherwise final output path.
        """
        return self._temp_wav_path if self._needs_conversion else self._output_path

    def _convert_if_needed(self) -> None:
        """Convert temp WAV to target format if needed."""
        if self._needs_conversion and self._temp_wav_path:
            self._convert_to_target_format(self._temp_wav_path)

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

    @abstractmethod
    def text_to_speech(self, text: str) -> None:
        """Convert text to speech and save to file."""
        ...
