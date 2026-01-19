"""Video service factory for creating video generators."""

from app.core.config import Settings
from app.integrations.video.base import VideoService
from app.integrations.video.ffmpeg_video import create_ffmpeg_video_service


class VideoFactory:
    """Factory for creating video service instances."""

    @staticmethod
    def create(settings: Settings) -> VideoService | None:
        """
        Create a video service if video generation is enabled.

        Args:
            settings: Application settings

        Returns:
            A VideoService implementation, or None if video is disabled
        """
        if not settings.video_enabled:
            return None

        return create_ffmpeg_video_service(settings)

    @staticmethod
    def create_from_settings(settings: Settings) -> VideoService | None:
        """Create video service using settings (alias for create)."""
        return VideoFactory.create(settings)
