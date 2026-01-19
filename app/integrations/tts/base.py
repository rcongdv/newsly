"""Base protocol and data classes for TTS services."""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class WordTiming:
    """Timing information for a single word."""

    word: str
    start_time: float  # seconds
    end_time: float  # seconds


@dataclass
class TTSResult:
    """Result from TTS generation including optional timing data."""

    audio_path: str
    word_timings: list[WordTiming] = field(default_factory=list)


@runtime_checkable
class TTSService(Protocol):
    """Protocol for text-to-speech services."""

    @property
    def output_path(self) -> str:
        """Return the actual output path where audio will be saved."""
        ...

    @property
    def word_timings(self) -> list[WordTiming]:
        """Return word timing data from last TTS generation (empty if not supported)."""
        ...

    def text_to_speech(self, text: str) -> None:
        """Convert text to speech and save to file."""
        ...
