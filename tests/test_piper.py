"""Tests for the PiperService in app.integrations.tts.piper."""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from app.integrations.tts.piper import PiperService, create_piper_service


class TestPiperService:
    """Tests for the PiperService class."""

    def test_init_with_wav_format(self):
        """Test initialization with native WAV format."""
        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.wav",
            speaker_id=0,
            length_scale=1.0,
            sentence_silence=0.2,
        )

        assert service._model_path == "/path/to/model.onnx"
        assert service._output_path == "test_output.wav"
        assert service.output_path == "test_output.wav"
        assert service._speaker_id == 0
        assert service._length_scale == 1.0
        assert service._sentence_silence == 0.2
        assert service._needs_conversion is False

    def test_init_with_mp3_format_sets_conversion_flag(self):
        """Test that MP3 format sets conversion flag."""
        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.mp3",
        )

        assert service._output_path == "test_output.mp3"
        assert service.output_path == "test_output.mp3"
        assert service._needs_conversion is True
        assert service._temp_wav_path == "test_output_temp.wav"

    def test_init_without_speaker_id(self):
        """Test initialization without speaker ID."""
        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.wav",
        )

        assert service._speaker_id is None

    @patch("app.integrations.tts.piper.wave.open")
    @patch("app.integrations.tts.piper.PiperService._get_voice")
    def test_text_to_speech_calls_piper_synthesize_wav(self, mock_get_voice, mock_wave_open):
        """Test that text_to_speech calls piper voice synthesize_wav."""
        mock_voice = MagicMock()
        mock_get_voice.return_value = mock_voice
        mock_wav_file = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wav_file

        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.wav",
            length_scale=1.0,
            sentence_silence=0.2,
        )

        service.text_to_speech("Hello world")

        mock_wave_open.assert_called_once_with("test_output.wav", "wb")
        mock_voice.synthesize_wav.assert_called_once_with("Hello world", mock_wav_file)

    @patch("app.integrations.tts.base.os.remove")
    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.piper.wave.open")
    @patch("app.integrations.tts.piper.PiperService._get_voice")
    def test_text_to_speech_converts_to_mp3(self, mock_get_voice, mock_wave_open, mock_audio_segment, mock_remove):
        """Test that text_to_speech converts temp audio to MP3 when needed."""
        mock_voice = MagicMock()
        mock_get_voice.return_value = mock_voice
        mock_wav_file = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wav_file
        mock_audio = MagicMock()
        mock_audio_segment.from_wav.return_value = mock_audio

        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.mp3",
        )

        service.text_to_speech("Hello world")

        # Should save to temp file first
        mock_wave_open.assert_called_once_with("test_output_temp.wav", "wb")

        # Should convert WAV to MP3
        mock_audio_segment.from_wav.assert_called_once_with("test_output_temp.wav")
        mock_audio.export.assert_called_once_with("test_output.mp3", format="mp3")

        # Should clean up temp file
        mock_remove.assert_called_once_with("test_output_temp.wav")

    def test_get_voice_raises_on_import_error(self):
        """Test that _get_voice raises TTSServiceError when piper not installed."""
        from app.core.exceptions import TTSServiceError

        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.wav",
        )

        with patch.dict("sys.modules", {"piper": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'piper'")):
                with pytest.raises(TTSServiceError) as exc_info:
                    service._get_voice()

        assert "piper-tts" in exc_info.value.detail.lower()

    @patch("app.integrations.tts.piper.wave.open")
    @patch("app.integrations.tts.piper.PiperService._get_voice")
    def test_text_to_speech_raises_on_synthesize_error(self, mock_get_voice, mock_wave_open):
        """Test that text_to_speech raises TTSServiceError on synthesis failure."""
        from app.core.exceptions import TTSServiceError

        mock_voice = MagicMock()
        mock_voice.synthesize_wav.side_effect = Exception("Synthesis error")
        mock_get_voice.return_value = mock_voice
        mock_wav_file = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wav_file

        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.wav",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")

    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.piper.wave.open")
    @patch("app.integrations.tts.piper.PiperService._get_voice")
    def test_text_to_speech_raises_on_conversion_error(self, mock_get_voice, mock_wave_open, mock_audio_segment):
        """Test that text_to_speech raises TTSServiceError on conversion failure."""
        from app.core.exceptions import TTSServiceError

        mock_voice = MagicMock()
        mock_get_voice.return_value = mock_voice
        mock_wav_file = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wav_file
        mock_audio_segment.from_wav.side_effect = Exception("Conversion error")

        service = PiperService(
            model_path="/path/to/model.onnx",
            output_path="test_output.mp3",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")


class TestCreatePiperService:
    """Tests for the create_piper_service factory function."""

    def test_create_piper_service_from_settings(self):
        """Test that create_piper_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.piper_model_path = "/models/en_US.onnx"
        mock_settings.tts_output_path = "output.mp3"
        mock_settings.piper_speaker_id = 1
        mock_settings.piper_length_scale = 0.9
        mock_settings.piper_sentence_silence = 0.3

        service = create_piper_service(mock_settings)

        assert isinstance(service, PiperService)
        assert service._model_path == "/models/en_US.onnx"
        assert service._output_path == "output.mp3"
        assert service._speaker_id == 1
        assert service._length_scale == 0.9
        assert service._sentence_silence == 0.3

    def test_create_piper_service_with_none_speaker_id(self):
        """Test that create_piper_service handles None speaker ID."""
        mock_settings = MagicMock()
        mock_settings.piper_model_path = "/models/en_US.onnx"
        mock_settings.tts_output_path = "output.wav"
        mock_settings.piper_speaker_id = None
        mock_settings.piper_length_scale = 1.0
        mock_settings.piper_sentence_silence = 0.2

        service = create_piper_service(mock_settings)

        assert isinstance(service, PiperService)
        assert service._speaker_id is None
