"""Tests for the CoquiService in app.integrations.tts.coqui."""

import pytest
from unittest.mock import MagicMock, patch

from app.integrations.tts.coqui import CoquiService, create_coqui_service


class TestCoquiService:
    """Tests for the CoquiService class."""

    def test_init_with_wav_format(self):
        """Test initialization with native WAV format."""
        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.wav",
            language="en",
            gpu=False,
        )

        assert service._model_name == "tts_models/en/ljspeech/tacotron2-DDC"
        assert service._output_path == "test_output.wav"
        assert service.output_path == "test_output.wav"
        assert service._language == "en"
        assert service._gpu is False
        assert service._needs_conversion is False
        assert service._tts is None  # Lazy initialization

    def test_init_with_mp3_format_sets_conversion_flag(self):
        """Test that MP3 format sets conversion flag."""
        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.mp3",
        )

        assert service._output_path == "test_output.mp3"
        assert service.output_path == "test_output.mp3"
        assert service._needs_conversion is True
        assert service._temp_wav_path == "test_output_temp.wav"

    def test_init_with_speaker_wav(self):
        """Test initialization with speaker WAV for voice cloning."""
        service = CoquiService(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            output_path="test_output.wav",
            speaker_wav="/path/to/speaker.wav",
            language="en",
        )

        assert service._speaker_wav == "/path/to/speaker.wav"

    def test_init_with_gpu_enabled(self):
        """Test initialization with GPU enabled."""
        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.wav",
            gpu=True,
        )

        assert service._gpu is True

    @patch("app.integrations.tts.coqui.CoquiService._get_tts")
    def test_text_to_speech_calls_tts_to_file(self, mock_get_tts):
        """Test that text_to_speech calls tts_to_file."""
        mock_tts = MagicMock()
        mock_tts.speakers = None  # Single speaker model
        mock_get_tts.return_value = mock_tts

        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.wav",
        )

        service.text_to_speech("Hello world")

        mock_tts.tts_to_file.assert_called_once_with(
            text="Hello world",
            file_path="test_output.wav",
        )

    @patch("app.integrations.tts.coqui.CoquiService._get_tts")
    def test_text_to_speech_with_voice_cloning(self, mock_get_tts):
        """Test text_to_speech with voice cloning (speaker_wav)."""
        mock_tts = MagicMock()
        mock_tts.speakers = ["speaker1"]  # Multi-speaker model
        mock_get_tts.return_value = mock_tts

        service = CoquiService(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            output_path="test_output.wav",
            speaker_wav="/path/to/speaker.wav",
            language="en",
        )

        service.text_to_speech("Hello world")

        mock_tts.tts_to_file.assert_called_once_with(
            text="Hello world",
            file_path="test_output.wav",
            speaker_wav="/path/to/speaker.wav",
            language="en",
        )

    @patch("app.integrations.tts.base.os.remove")
    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.coqui.CoquiService._get_tts")
    def test_text_to_speech_converts_to_mp3(self, mock_get_tts, mock_audio_segment, mock_remove):
        """Test that text_to_speech converts temp audio to MP3 when needed."""
        mock_tts = MagicMock()
        mock_tts.speakers = None
        mock_get_tts.return_value = mock_tts

        mock_audio = MagicMock()
        mock_audio_segment.from_wav.return_value = mock_audio

        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.mp3",
        )

        service.text_to_speech("Hello world")

        # Should save to temp file first
        mock_tts.tts_to_file.assert_called_once()
        call_kwargs = mock_tts.tts_to_file.call_args[1]
        assert call_kwargs["file_path"] == "test_output_temp.wav"

        # Should convert WAV to MP3
        mock_audio_segment.from_wav.assert_called_once_with("test_output_temp.wav")
        mock_audio.export.assert_called_once_with("test_output.mp3", format="mp3")

        # Should clean up temp file
        mock_remove.assert_called_once_with("test_output_temp.wav")

    def test_get_tts_raises_on_import_error(self):
        """Test that _get_tts raises TTSServiceError when TTS not installed."""
        from app.core.exceptions import TTSServiceError

        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.wav",
        )

        with patch.dict("sys.modules", {"TTS": None, "TTS.api": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'TTS'")):
                with pytest.raises(TTSServiceError) as exc_info:
                    service._get_tts()

                assert "not installed" in exc_info.value.message.lower()

    @patch("app.integrations.tts.coqui.CoquiService._get_tts")
    def test_text_to_speech_raises_on_error(self, mock_get_tts):
        """Test that text_to_speech raises TTSServiceError on failure."""
        from app.core.exceptions import TTSServiceError

        mock_tts = MagicMock()
        mock_tts.speakers = None
        mock_tts.tts_to_file.side_effect = Exception("TTS generation failed")
        mock_get_tts.return_value = mock_tts

        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.wav",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")

    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.coqui.CoquiService._get_tts")
    def test_text_to_speech_raises_on_conversion_error(self, mock_get_tts, mock_audio_segment):
        """Test that text_to_speech raises TTSServiceError on conversion failure."""
        from app.core.exceptions import TTSServiceError

        mock_tts = MagicMock()
        mock_tts.speakers = None
        mock_get_tts.return_value = mock_tts

        mock_audio_segment.from_wav.side_effect = Exception("Conversion error")

        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.mp3",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")

    @patch("app.integrations.tts.coqui.CoquiService._get_tts")
    def test_is_multispeaker_model_returns_true(self, mock_get_tts):
        """Test _is_multispeaker_model returns True for multi-speaker models."""
        mock_tts = MagicMock()
        mock_tts.speakers = ["speaker1", "speaker2"]
        mock_get_tts.return_value = mock_tts

        service = CoquiService(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            output_path="test_output.wav",
        )

        assert service._is_multispeaker_model() is True

    @patch("app.integrations.tts.coqui.CoquiService._get_tts")
    def test_is_multispeaker_model_returns_false(self, mock_get_tts):
        """Test _is_multispeaker_model returns False for single-speaker models."""
        mock_tts = MagicMock()
        mock_tts.speakers = None
        mock_get_tts.return_value = mock_tts

        service = CoquiService(
            model_name="tts_models/en/ljspeech/tacotron2-DDC",
            output_path="test_output.wav",
        )

        assert service._is_multispeaker_model() is False


class TestCreateCoquiService:
    """Tests for the create_coqui_service factory function."""

    def test_create_coqui_service_from_settings(self):
        """Test that create_coqui_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.coqui_model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        mock_settings.tts_output_path = "output.mp3"
        mock_settings.coqui_speaker_wav = None
        mock_settings.tts_language = "en"
        mock_settings.coqui_use_gpu = False

        service = create_coqui_service(mock_settings)

        assert isinstance(service, CoquiService)
        assert service._model_name == "tts_models/en/ljspeech/tacotron2-DDC"
        assert service._output_path == "output.mp3"
        assert service._speaker_wav is None
        assert service._language == "en"
        assert service._gpu is False

    def test_create_coqui_service_with_voice_cloning(self):
        """Test that create_coqui_service handles voice cloning settings."""
        mock_settings = MagicMock()
        mock_settings.coqui_model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        mock_settings.tts_output_path = "output.wav"
        mock_settings.coqui_speaker_wav = "/path/to/voice.wav"
        mock_settings.tts_language = "es"
        mock_settings.coqui_use_gpu = True

        service = create_coqui_service(mock_settings)

        assert isinstance(service, CoquiService)
        assert service._speaker_wav == "/path/to/voice.wav"
        assert service._language == "es"
        assert service._gpu is True
