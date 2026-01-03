"""Abstract base class for TTS services."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TTSService(Protocol):
    """Protocol for text-to-speech services."""

    def text_to_speech(self, text: str) -> None:
        """Convert text to speech and save to file."""
        ...
