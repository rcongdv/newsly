"""Tests for the ElevenLabsService in app.integrations.tts.elevenlabs."""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from app.integrations.tts.elevenlabs import ElevenLabsService, create_elevenlabs_service


class TestElevenLabsService:
    """Tests for the ElevenLabsService class."""

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_init_success(self, mock_elevenlabs_client):
        """Test successful initialization of ElevenLabsService."""
        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        mock_elevenlabs_client.assert_called_once_with(api_key="test-api-key")
        assert service._voice_id == "test-voice-id"
        assert service._model_id == "test-model-id"
        assert service._output_path == "test_output.mp3"

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_calls_api(self, mock_elevenlabs_client):
        """Test that text_to_speech calls the ElevenLabs API with correct parameters."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert.return_value = iter([b"audio", b"data"])

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            service.text_to_speech("Hello world")

            mock_client_instance.text_to_speech.convert.assert_called_once_with(
                text="Hello world",
                voice_id="test-voice-id",
                model_id="test-model-id",
            )

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_writes_to_file(self, mock_elevenlabs_client):
        """Test that text_to_speech writes audio bytes to the correct file."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert.return_value = iter([b"audio", b"data"])

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            service.text_to_speech("Hello world")

            mocked_file.assert_called_once_with("test_output.mp3", "wb")
            mocked_file().write.assert_called_once_with(b"audiodata")

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_joins_audio_chunks(self, mock_elevenlabs_client):
        """Test that audio generator chunks are properly joined."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert.return_value = iter(
            [b"chunk1", b"chunk2", b"chunk3"]
        )

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            service.text_to_speech("Test")

            mocked_file().write.assert_called_once_with(b"chunk1chunk2chunk3")

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_raises_on_error(self, mock_elevenlabs_client):
        """Test that text_to_speech raises TTSServiceError on failure."""
        from app.core.exceptions import TTSServiceError

        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert.side_effect = Exception("API Error")

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")


class TestCreateElevenLabsService:
    """Tests for the create_elevenlabs_service factory function."""

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_create_elevenlabs_service_from_settings(self, mock_elevenlabs_client):
        """Test that create_elevenlabs_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.elevenlabs_api_key = "settings-api-key"
        mock_settings.elevenlabs_voice_id = "settings-voice-id"
        mock_settings.elevenlabs_model_id = "settings-model-id"
        mock_settings.tts_output_path = "settings_output.mp3"

        service = create_elevenlabs_service(mock_settings)

        assert isinstance(service, ElevenLabsService)
        mock_elevenlabs_client.assert_called_once_with(api_key="settings-api-key")
