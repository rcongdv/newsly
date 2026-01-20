"""Base class and protocol for video services."""

from typing import Protocol, runtime_checkable

from app.integrations.tts.base import WordTiming


@runtime_checkable
class VideoService(Protocol):
    """Protocol for video generation services."""

    @property
    def output_path(self) -> str:
        """Return the output path where video will be saved."""
        ...

    def create_video(
        self,
        audio_path: str,
        text: str,
        word_timings: list[WordTiming] | None = None,
    ) -> None:
        """
        Create a video with subtitles from audio and text.

        Args:
            audio_path: Path to the audio file
            text: Text content for generating subtitles (used if word_timings not provided)
            word_timings: Optional word-level timing data from TTS for accurate subtitles
        """
        ...
