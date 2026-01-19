"""Tests for the VideoFactory in app.integrations.video.factory."""

import pytest
from unittest.mock import MagicMock, patch

from app.integrations.video.factory import VideoFactory
from app.integrations.video.ffmpeg_video import FFmpegVideoService


class TestVideoFactory:
    """Tests for the VideoFactory class."""

    @patch("app.integrations.video.factory.create_ffmpeg_video_service")
    def test_create_returns_service_when_enabled(self, mock_create_ffmpeg):
        """Test that create returns FFmpeg service when video is enabled."""
        mock_service = MagicMock(spec=FFmpegVideoService)
        mock_create_ffmpeg.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.video_enabled = True

        result = VideoFactory.create(mock_settings)

        mock_create_ffmpeg.assert_called_once_with(mock_settings)
        assert result is mock_service

    def test_create_returns_none_when_disabled(self):
        """Test that create returns None when video is disabled."""
        mock_settings = MagicMock()
        mock_settings.video_enabled = False

        result = VideoFactory.create(mock_settings)

        assert result is None

    @patch("app.integrations.video.factory.create_ffmpeg_video_service")
    def test_create_from_settings_when_enabled(self, mock_create_ffmpeg):
        """Test that create_from_settings returns service when enabled."""
        mock_service = MagicMock(spec=FFmpegVideoService)
        mock_create_ffmpeg.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.video_enabled = True

        result = VideoFactory.create_from_settings(mock_settings)

        mock_create_ffmpeg.assert_called_once_with(mock_settings)
        assert result is mock_service

    def test_create_from_settings_when_disabled(self):
        """Test that create_from_settings returns None when disabled."""
        mock_settings = MagicMock()
        mock_settings.video_enabled = False

        result = VideoFactory.create_from_settings(mock_settings)

        assert result is None

    @patch("app.integrations.video.factory.create_ffmpeg_video_service")
    def test_create_passes_settings_to_factory_function(self, mock_create_ffmpeg):
        """Test that settings are passed to the FFmpeg factory function."""
        mock_settings = MagicMock()
        mock_settings.video_enabled = True
        mock_settings.video_output_file = "test_output"
        mock_settings.video_output_format = "mp4"

        VideoFactory.create(mock_settings)

        # Verify settings object was passed
        call_args = mock_create_ffmpeg.call_args
        assert call_args[0][0] is mock_settings
