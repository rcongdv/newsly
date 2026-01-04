"""Tests for the PyTTSService in app.integrations.tts.pytts."""

import pytest
from unittest.mock import MagicMock, patch, call

from app.integrations.tts.pytts import PyTTSService, create_pytts_service


class TestPyTTSService:
    """Tests for the PyTTSService class."""

    def test_init_with_wav_format(self):
        """Test initialization with native WAV format."""
        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.wav",
        )

        assert service._voice_rate == 150
        assert service._volume == 0.9
        assert service._voice_id == "0"
        assert service._output_path == "test_output.wav"
        assert service.output_path == "test_output.wav"
        assert service._needs_conversion is False

    def test_init_with_mp3_format_sets_conversion_flag(self):
        """Test that MP3 format sets conversion flag."""
        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.mp3",
        )

        assert service._output_path == "test_output.mp3"
        assert service.output_path == "test_output.mp3"
        assert service._needs_conversion is True
        assert service._temp_wav_path == "test_output_temp.wav"

    def test_init_with_aiff_format_needs_conversion(self):
        """Test initialization with AIFF format requires conversion."""
        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.aiff",
        )

        assert service._output_path == "test_output.aiff"
        assert service._needs_conversion is True

    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_initializes_engine(self, mock_pyttsx3_init):
        """Test that text_to_speech initializes a new engine each time."""
        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.id = "voice-id-0"
        mock_engine.getProperty.return_value = [mock_voice]
        mock_pyttsx3_init.return_value = mock_engine

        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.wav",
        )

        service.text_to_speech("Hello world")

        mock_pyttsx3_init.assert_called_once()

    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_sets_properties(self, mock_pyttsx3_init):
        """Test that text_to_speech sets engine properties correctly."""
        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.id = "voice-id-0"
        mock_engine.getProperty.return_value = [mock_voice]
        mock_pyttsx3_init.return_value = mock_engine

        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.wav",
        )

        service.text_to_speech("Hello world")

        mock_engine.setProperty.assert_any_call("rate", 150)
        mock_engine.setProperty.assert_any_call("volume", 0.9)
        mock_engine.setProperty.assert_any_call("voice", "voice-id-0")

    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_saves_to_file_wav(self, mock_pyttsx3_init):
        """Test that text_to_speech saves audio directly for WAV format."""
        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.id = "voice-id-0"
        mock_engine.getProperty.return_value = [mock_voice]
        mock_pyttsx3_init.return_value = mock_engine

        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.wav",
        )

        service.text_to_speech("Hello world")

        mock_engine.save_to_file.assert_called_once_with("Hello world", "test_output.wav")

    @patch("app.integrations.tts.base.os.remove")
    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_converts_to_mp3(self, mock_pyttsx3_init, mock_audio_segment, mock_remove):
        """Test that text_to_speech converts temp audio to MP3 when needed."""
        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.id = "voice-id-0"
        mock_engine.getProperty.return_value = [mock_voice]
        mock_pyttsx3_init.return_value = mock_engine

        mock_audio = MagicMock()
        mock_audio_segment.from_wav.return_value = mock_audio

        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.mp3",
        )

        service.text_to_speech("Hello world")

        # Should save to temp file first
        mock_engine.save_to_file.assert_called_once_with("Hello world", "test_output_temp.wav")

        # Should convert WAV to MP3
        mock_audio_segment.from_wav.assert_called_once_with("test_output_temp.wav")
        mock_audio.export.assert_called_once_with("test_output.mp3", format="mp3")

        # Should clean up temp file
        mock_remove.assert_called_once_with("test_output_temp.wav")

    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_runs_and_stops(self, mock_pyttsx3_init):
        """Test that text_to_speech calls runAndWait and stop."""
        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.id = "voice-id-0"
        mock_engine.getProperty.return_value = [mock_voice]
        mock_pyttsx3_init.return_value = mock_engine

        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.wav",
        )

        service.text_to_speech("Test")

        mock_engine.runAndWait.assert_called_once()
        mock_engine.stop.assert_called_once()

    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_with_different_voice_id(self, mock_pyttsx3_init):
        """Test text_to_speech with a different voice ID."""
        mock_engine = MagicMock()
        mock_voice_0 = MagicMock()
        mock_voice_0.id = "voice-id-0"
        mock_voice_1 = MagicMock()
        mock_voice_1.id = "voice-id-1"
        mock_engine.getProperty.return_value = [mock_voice_0, mock_voice_1]
        mock_pyttsx3_init.return_value = mock_engine

        service = PyTTSService(
            voice_rate=200,
            volume=1.0,
            voice_id="1",
            output_path="output.wav",
        )

        service.text_to_speech("Test")

        mock_engine.setProperty.assert_any_call("voice", "voice-id-1")

    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_raises_on_error(self, mock_pyttsx3_init):
        """Test that text_to_speech raises TTSServiceError on failure."""
        from app.core.exceptions import TTSServiceError

        mock_pyttsx3_init.side_effect = Exception("Engine init error")

        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.wav",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")

    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.pytts.pyttsx3.init")
    def test_text_to_speech_raises_on_conversion_error(self, mock_pyttsx3_init, mock_audio_segment):
        """Test that text_to_speech raises TTSServiceError on conversion failure."""
        from app.core.exceptions import TTSServiceError

        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.id = "voice-id-0"
        mock_engine.getProperty.return_value = [mock_voice]
        mock_pyttsx3_init.return_value = mock_engine

        mock_audio_segment.from_wav.side_effect = Exception("Conversion error")

        service = PyTTSService(
            voice_rate=150,
            volume=0.9,
            voice_id="0",
            output_path="test_output.mp3",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")


class TestCreatePyTTSService:
    """Tests for the create_pytts_service factory function."""

    def test_create_pytts_service_from_settings_with_wav(self):
        """Test that create_pytts_service creates service from settings with WAV format."""
        mock_settings = MagicMock()
        mock_settings.pytts_voice_rate = 125
        mock_settings.pytts_volume = 1.0
        mock_settings.pytts_voice_id = "0"
        mock_settings.tts_output_path = "settings_output.wav"

        service = create_pytts_service(mock_settings)

        assert isinstance(service, PyTTSService)
        assert service._voice_rate == 125
        assert service._volume == 1.0
        assert service._voice_id == "0"
        assert service._output_path == "settings_output.wav"

    def test_create_pytts_service_with_mp3(self):
        """Test that create_pytts_service handles MP3 format."""
        mock_settings = MagicMock()
        mock_settings.pytts_voice_rate = 125
        mock_settings.pytts_volume = 1.0
        mock_settings.pytts_voice_id = "0"
        mock_settings.tts_output_path = "settings_output.mp3"

        service = create_pytts_service(mock_settings)

        assert isinstance(service, PyTTSService)
        # MP3 is kept as the output path
        assert service._output_path == "settings_output.mp3"
        assert service.output_path == "settings_output.mp3"
        assert service._needs_conversion is True
