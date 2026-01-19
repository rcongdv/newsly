"""FFmpeg-based video generation service."""

import json
import logging
import os
import subprocess
import tempfile

import ffmpeg

from app.core.config import Settings
from app.core.exceptions import VideoServiceError
from app.integrations.video.subtitle import (
    generate_srt_content,
    split_text_into_segments,
)

logger = logging.getLogger(__name__)


class FFmpegVideoService:
    """Video service using FFmpeg for video generation with subtitles."""

    def __init__(
        self,
        output_path: str,
        width: int = 1080,
        height: int = 1080,
        background_color: str = "#1a1a2e",
        background_image: str | None = None,
        subtitle_font_size: int = 48,
        subtitle_font_color: str = "white",
        subtitle_max_chars: int = 60,
    ):
        """
        Initialize FFmpeg video service.

        Args:
            output_path: Path for the output video file
            width: Video width in pixels
            height: Video height in pixels
            background_color: Hex color for background (e.g., "#1a1a2e")
            background_image: Optional path to background image
            subtitle_font_size: Font size for subtitles
            subtitle_font_color: Color name for subtitles
            subtitle_max_chars: Maximum characters per subtitle line
        """
        self._output_path = output_path
        self._width = width
        self._height = height
        self._background_color = background_color
        self._background_image = background_image
        self._subtitle_font_size = subtitle_font_size
        self._subtitle_font_color = subtitle_font_color
        self._subtitle_max_chars = subtitle_max_chars

    @property
    def output_path(self) -> str:
        """Return the output path where video will be saved."""
        return self._output_path

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    audio_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get audio duration: {e}")
            raise VideoServiceError(
                "Failed to get audio duration",
                detail=str(e),
            ) from e

    def _escape_srt_path(self, path: str) -> str:
        """Escape special characters in subtitle path for FFmpeg filter."""
        # FFmpeg subtitles filter requires escaping of special chars
        # Backslashes and colons need escaping
        escaped = path.replace("\\", "\\\\")
        escaped = escaped.replace(":", "\\:")
        escaped = escaped.replace("'", "\\'")
        return escaped

    def create_video(self, audio_path: str, text: str) -> None:
        """
        Create a video with burned-in subtitles.

        Args:
            audio_path: Path to the audio file
            text: Text content for generating subtitles

        Raises:
            VideoServiceError: If video creation fails
        """
        logger.info(f"Creating video from audio: {audio_path}")

        # Get audio duration
        duration = self._get_audio_duration(audio_path)
        logger.info(f"Audio duration: {duration:.2f} seconds")

        # Generate subtitles
        subtitle_entries = split_text_into_segments(
            text,
            audio_duration=duration,
            max_chars_per_line=self._subtitle_max_chars,
        )
        srt_content = generate_srt_content(subtitle_entries)
        logger.info(f"Generated {len(subtitle_entries)} subtitle segments")

        # Create temp file for SRT
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".srt",
            delete=False,
            encoding="utf-8",
        ) as srt_file:
            srt_file.write(srt_content)
            srt_path = srt_file.name

        try:
            self._create_video_with_ffmpeg(audio_path, srt_path, duration)
            logger.info(f"Video created successfully: {self._output_path}")
        finally:
            # Clean up temp SRT file
            if os.path.exists(srt_path):
                os.remove(srt_path)

    def _create_video_with_ffmpeg(
        self,
        audio_path: str,
        srt_path: str,
        duration: float,
    ) -> None:
        """Create video using FFmpeg with subtitles burned in."""
        try:
            # Convert hex color to FFmpeg format (remove # prefix)
            bg_color = self._background_color.lstrip("#")

            # Build subtitle filter with styling
            escaped_srt = self._escape_srt_path(srt_path)
            subtitle_filter = (
                f"subtitles={escaped_srt}:force_style='"
                f"FontSize={self._subtitle_font_size},"
                f"PrimaryColour=&H00FFFFFF,"  # White in ASS format (AABBGGRR)
                f"OutlineColour=&H00000000,"  # Black outline
                f"Outline=2,"
                f"Alignment=2,"  # Center bottom
                f"MarginV=50'"  # Margin from bottom
            )

            if self._background_image and os.path.exists(self._background_image):
                # Use background image
                video_input = ffmpeg.input(
                    self._background_image,
                    loop=1,
                    t=duration,
                )
                video_input = video_input.filter(
                    "scale",
                    self._width,
                    self._height,
                )
            else:
                # Create solid color background
                video_input = ffmpeg.input(
                    f"color=c={bg_color}:s={self._width}x{self._height}:d={duration}",
                    f="lavfi",
                )

            # Input audio
            audio_input = ffmpeg.input(audio_path)

            # Apply subtitle filter and combine with audio
            video_with_subs = video_input.filter(
                "subtitles",
                srt_path,
                force_style=(
                    f"FontSize={self._subtitle_font_size},"
                    f"PrimaryColour=&H00FFFFFF,"
                    f"OutlineColour=&H00000000,"
                    f"Outline=2,"
                    f"Alignment=2,"
                    f"MarginV=50"
                ),
            )

            # Output with audio
            output = ffmpeg.output(
                video_with_subs,
                audio_input,
                self._output_path,
                vcodec="libx264",
                acodec="aac",
                pix_fmt="yuv420p",
                shortest=None,
            )

            # Run FFmpeg
            output.overwrite_output().run(capture_stdout=True, capture_stderr=True)

        except ffmpeg.Error as e:
            stderr = e.stderr.decode() if e.stderr else "Unknown error"
            logger.error(f"FFmpeg error: {stderr}")
            raise VideoServiceError(
                "Failed to create video with FFmpeg",
                detail=stderr,
            ) from e
        except Exception as e:
            logger.error(f"Video creation error: {e}")
            raise VideoServiceError(
                "Failed to create video",
                detail=str(e),
            ) from e


def create_ffmpeg_video_service(settings: Settings) -> FFmpegVideoService:
    """
    Factory function to create FFmpegVideoService from settings.

    Args:
        settings: Application settings

    Returns:
        Configured FFmpegVideoService instance
    """
    output_path = f"{settings.video_output_file}.{settings.video_output_format}"

    return FFmpegVideoService(
        output_path=output_path,
        width=settings.video_width,
        height=settings.video_height,
        background_color=settings.video_background_color,
        background_image=settings.video_background_image,
        subtitle_font_size=settings.subtitle_font_size,
        subtitle_font_color=settings.subtitle_font_color,
        subtitle_max_chars=settings.subtitle_max_chars_per_line,
    )
