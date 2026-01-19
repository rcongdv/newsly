"""Tests for the FFmpegVideoService in app.integrations.video.ffmpeg_video."""

import json
import pytest
from unittest.mock import MagicMock, patch, mock_open

from app.integrations.video.ffmpeg_video import (
    FFmpegVideoService,
    create_ffmpeg_video_service,
)
from app.core.exceptions import VideoServiceError


class TestFFmpegVideoService:
    """Tests for the FFmpegVideoService class."""

    def test_init(self):
        """Test service initialization with default values."""
        service = FFmpegVideoService(
            output_path="output.mp4",
        )

        assert service._output_path == "output.mp4"
        assert service._width == 1080
        assert service._height == 1080
        assert service._background_color == "#1a1a2e"
        assert service._background_image is None
        assert service._subtitle_font_size == 40
        assert service._subtitle_font_color == "white"
        assert service._subtitle_max_chars == 45

    def test_init_with_custom_values(self):
        """Test service initialization with custom values."""
        service = FFmpegVideoService(
            output_path="custom.mp4",
            width=1920,
            height=1080,
            background_color="#000000",
            background_image="/path/to/bg.jpg",
            subtitle_font_size=36,
            subtitle_font_color="yellow",
            subtitle_max_chars=80,
        )

        assert service._output_path == "custom.mp4"
        assert service._width == 1920
        assert service._height == 1080
        assert service._background_color == "#000000"
        assert service._background_image == "/path/to/bg.jpg"
        assert service._subtitle_font_size == 36
        assert service._subtitle_font_color == "yellow"
        assert service._subtitle_max_chars == 80

    def test_output_path_property(self):
        """Test output_path property returns correct path."""
        service = FFmpegVideoService(output_path="test_video.mp4")
        assert service.output_path == "test_video.mp4"

    @patch("app.integrations.video.ffmpeg_video.subprocess.run")
    def test_get_audio_duration_success(self, mock_run):
        """Test getting audio duration with ffprobe."""
        mock_run.return_value = MagicMock(
            stdout='{"format": {"duration": "10.5"}}',
            returncode=0,
        )

        service = FFmpegVideoService(output_path="output.mp4")
        duration = service._get_audio_duration("/path/to/audio.mp3")

        assert duration == 10.5
        mock_run.assert_called_once()

    @patch("app.integrations.video.ffmpeg_video.subprocess.run")
    def test_get_audio_duration_failure(self, mock_run):
        """Test that audio duration failure raises VideoServiceError."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe")

        service = FFmpegVideoService(output_path="output.mp4")

        with pytest.raises(VideoServiceError):
            service._get_audio_duration("/path/to/audio.mp3")

    def test_escape_srt_path(self):
        """Test SRT path escaping for FFmpeg filter."""
        service = FFmpegVideoService(output_path="output.mp4")

        # Test backslash escaping
        assert "\\\\" in service._escape_srt_path("path\\to\\file.srt")

        # Test colon escaping
        assert "\\:" in service._escape_srt_path("C:/path/file.srt")

        # Test single quote escaping
        assert "\\'" in service._escape_srt_path("path/it's.srt")

    @patch("app.integrations.video.ffmpeg_video.os.path.exists")
    @patch("app.integrations.video.ffmpeg_video.os.remove")
    @patch("app.integrations.video.ffmpeg_video.ffmpeg")
    @patch("app.integrations.video.ffmpeg_video.subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("tempfile.NamedTemporaryFile")
    def test_create_video_success(
        self,
        mock_tempfile,
        mock_open_file,
        mock_run,
        mock_ffmpeg,
        mock_remove,
        mock_exists,
    ):
        """Test successful video creation."""
        # Setup mocks
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.srt"
        mock_temp.__enter__ = MagicMock(return_value=mock_temp)
        mock_temp.__exit__ = MagicMock(return_value=False)
        mock_tempfile.return_value = mock_temp

        mock_run.return_value = MagicMock(
            stdout='{"format": {"duration": "10.0"}}',
            returncode=0,
        )

        mock_exists.return_value = True

        # Mock FFmpeg chain
        mock_input = MagicMock()
        mock_filter = MagicMock()
        mock_output = MagicMock()
        mock_overwrite = MagicMock()

        mock_ffmpeg.input.return_value = mock_input
        mock_input.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_ffmpeg.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite

        service = FFmpegVideoService(output_path="output.mp4")
        service.create_video("/path/to/audio.mp3", "Test subtitle text.")

        # Verify FFmpeg was called
        assert mock_ffmpeg.input.called
        assert mock_ffmpeg.output.called
        mock_overwrite.run.assert_called_once()

    @patch("app.integrations.video.ffmpeg_video.os.path.exists")
    @patch("app.integrations.video.ffmpeg_video.os.remove")
    @patch("app.integrations.video.ffmpeg_video.ffmpeg")
    @patch("app.integrations.video.ffmpeg_video.subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    def test_create_video_ffmpeg_error(
        self,
        mock_tempfile,
        mock_run,
        mock_ffmpeg,
        mock_remove,
        mock_exists,
    ):
        """Test that FFmpeg errors raise VideoServiceError."""
        import ffmpeg as real_ffmpeg

        # Setup temp file mock
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.srt"
        mock_temp.__enter__ = MagicMock(return_value=mock_temp)
        mock_temp.__exit__ = MagicMock(return_value=False)
        mock_tempfile.return_value = mock_temp

        mock_run.return_value = MagicMock(
            stdout='{"format": {"duration": "10.0"}}',
            returncode=0,
        )

        mock_exists.return_value = True

        # Mock the FFmpeg chain to raise error at run()
        mock_input = MagicMock()
        mock_filter = MagicMock()
        mock_output = MagicMock()
        mock_overwrite = MagicMock()

        mock_ffmpeg.input.return_value = mock_input
        mock_input.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_ffmpeg.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite
        # Use the real ffmpeg.Error class
        mock_ffmpeg.Error = real_ffmpeg.Error
        mock_overwrite.run.side_effect = real_ffmpeg.Error(
            "cmd", b"stdout", b"FFmpeg error"
        )

        service = FFmpegVideoService(output_path="output.mp4")

        with pytest.raises(VideoServiceError):
            service.create_video("/path/to/audio.mp3", "Test text.")


class TestCreateFFmpegVideoService:
    """Tests for the create_ffmpeg_video_service factory function."""

    def test_create_from_settings(self):
        """Test creating service from settings."""
        mock_settings = MagicMock()
        mock_settings.video_output_file = "my_video"
        mock_settings.video_output_format = "mp4"
        mock_settings.video_width = 1920
        mock_settings.video_height = 1080
        mock_settings.video_background_color = "#ffffff"
        mock_settings.video_background_image = None
        mock_settings.subtitle_font_size = 32
        mock_settings.subtitle_font_color = "black"
        mock_settings.subtitle_max_chars_per_line = 50

        service = create_ffmpeg_video_service(mock_settings)

        assert isinstance(service, FFmpegVideoService)
        assert service._output_path == "my_video.mp4"
        assert service._width == 1920
        assert service._height == 1080
        assert service._background_color == "#ffffff"
        assert service._subtitle_font_size == 32
        assert service._subtitle_max_chars == 50

    def test_create_with_background_image(self):
        """Test creating service with background image setting."""
        mock_settings = MagicMock()
        mock_settings.video_output_file = "output"
        mock_settings.video_output_format = "mp4"
        mock_settings.video_width = 1080
        mock_settings.video_height = 1080
        mock_settings.video_background_color = "#1a1a2e"
        mock_settings.video_background_image = "/path/to/image.jpg"
        mock_settings.subtitle_font_size = 48
        mock_settings.subtitle_font_color = "white"
        mock_settings.subtitle_max_chars_per_line = 60

        service = create_ffmpeg_video_service(mock_settings)

        assert service._background_image == "/path/to/image.jpg"
