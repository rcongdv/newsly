"""Tests for the PocketTTSService in app.integrations.tts.pocket_tts."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import numpy as np

from app.integrations.tts.pocket_tts import PocketTTSService, create_pocket_tts_service


class TestPocketTTSService:
    """Tests for the PocketTTSService class."""

    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_init_loads_model_and_voice(self, mock_tts_model_cls):
        """Test that init loads the model and voice state."""
        mock_model = MagicMock()
        mock_tts_model_cls.load_model.return_value = mock_model
        mock_voice_state = MagicMock()
        mock_model.get_state_for_audio_prompt.return_value = mock_voice_state

        service = PocketTTSService(voice="alba", output_path="output.wav")

        mock_tts_model_cls.load_model.assert_called_once()
        mock_model.get_state_for_audio_prompt.assert_called_once_with("alba")
        assert service._model is mock_model
        assert service._voice_state is mock_voice_state

    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_output_path(self, mock_tts_model_cls):
        """Test that output_path returns the configured path."""
        service = PocketTTSService(voice="alba", output_path="test_output.wav")
        assert service.output_path == "test_output.wav"

    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_word_timings_always_empty(self, mock_tts_model_cls):
        """Test that word_timings always returns an empty list."""
        service = PocketTTSService(voice="alba", output_path="output.wav")
        assert service.word_timings == []

    @patch("app.integrations.tts.pocket_tts.scipy.io.wavfile")
    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_text_to_speech_generates_and_saves_audio(
        self, mock_tts_model_cls, mock_wavfile
    ):
        """Test that text_to_speech generates audio and writes WAV file."""
        mock_model = MagicMock()
        mock_tts_model_cls.load_model.return_value = mock_model
        mock_voice_state = MagicMock()
        mock_model.get_state_for_audio_prompt.return_value = mock_voice_state

        # Mock audio tensor
        mock_audio = MagicMock()
        mock_audio_np = np.array([0.1, 0.2, 0.3])
        mock_audio.numpy.return_value = mock_audio_np
        mock_model.generate_audio.return_value = mock_audio
        mock_model.sample_rate = 24000

        service = PocketTTSService(voice="alba", output_path="test_output.wav")
        service.text_to_speech("Hello world")

        mock_model.generate_audio.assert_called_once_with(
            mock_voice_state, "Hello world"
        )
        mock_wavfile.write.assert_called_once_with(
            "test_output.wav",
            24000,
            mock_audio_np,
        )

    @patch("app.integrations.tts.pocket_tts.scipy.io.wavfile")
    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_text_to_speech_word_timings_remain_empty_after_generation(
        self, mock_tts_model_cls, mock_wavfile
    ):
        """Test that word_timings is still empty after generating audio."""
        mock_model = MagicMock()
        mock_tts_model_cls.load_model.return_value = mock_model
        mock_audio = MagicMock()
        mock_audio.numpy.return_value = np.array([0.0])
        mock_model.generate_audio.return_value = mock_audio

        service = PocketTTSService(voice="alba", output_path="output.wav")
        service.text_to_speech("Test")

        assert service.word_timings == []

    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_text_to_speech_raises_on_error(self, mock_tts_model_cls):
        """Test that text_to_speech raises TTSServiceError on failure."""
        from app.core.exceptions import TTSServiceError

        mock_model = MagicMock()
        mock_tts_model_cls.load_model.return_value = mock_model
        mock_model.generate_audio.side_effect = RuntimeError("Model error")

        service = PocketTTSService(voice="alba", output_path="output.wav")

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")

    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_init_with_custom_voice_path(self, mock_tts_model_cls):
        """Test initialization with a file path as voice."""
        mock_model = MagicMock()
        mock_tts_model_cls.load_model.return_value = mock_model

        service = PocketTTSService(
            voice="/path/to/custom_voice.wav", output_path="output.wav"
        )

        mock_model.get_state_for_audio_prompt.assert_called_once_with(
            "/path/to/custom_voice.wav"
        )


class TestCreatePocketTTSService:
    """Tests for the create_pocket_tts_service factory function."""

    @patch("app.integrations.tts.pocket_tts.TTSModel")
    def test_create_pocket_tts_service_from_settings(self, mock_tts_model_cls):
        """Test that create_pocket_tts_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.pocket_tts_voice = "marius"
        mock_settings.tts_output_path = "settings_output.wav"

        service = create_pocket_tts_service(mock_settings)

        assert isinstance(service, PocketTTSService)
        assert service.output_path == "settings_output.wav"
        mock_tts_model_cls.load_model.return_value.get_state_for_audio_prompt.assert_called_once_with(
            "marius"
        )
