"""Tests for the ElevenLabsService in app.integrations.tts.elevenlabs."""

import base64

import pytest
from unittest.mock import MagicMock, patch, mock_open

from app.integrations.tts.elevenlabs import ElevenLabsService, create_elevenlabs_service
from app.integrations.tts.base import WordTiming


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
        assert service.word_timings == []

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_calls_api_with_timestamps(self, mock_elevenlabs_client):
        """Test that text_to_speech calls convert_with_timestamps API."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance

        # Mock response with alignment data
        mock_response = MagicMock()
        mock_response.audio_base_64 = base64.b64encode(b"audio_data").decode()
        mock_response.alignment = MagicMock()
        mock_response.alignment.characters = list("Hello")
        mock_response.alignment.character_start_times_seconds = [0.0, 0.1, 0.2, 0.3, 0.4]
        mock_response.alignment.character_end_times_seconds = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_client_instance.text_to_speech.convert_with_timestamps.return_value = mock_response

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            service.text_to_speech("Hello")

            mock_client_instance.text_to_speech.convert_with_timestamps.assert_called_once_with(
                text="Hello",
                voice_id="test-voice-id",
                model_id="test-model-id",
            )

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_writes_decoded_audio(self, mock_elevenlabs_client):
        """Test that text_to_speech decodes base64 audio and writes to file."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance

        audio_bytes = b"test_audio_content"
        mock_response = MagicMock()
        mock_response.audio_base_64 = base64.b64encode(audio_bytes).decode()
        mock_response.alignment = None
        mock_client_instance.text_to_speech.convert_with_timestamps.return_value = mock_response

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            service.text_to_speech("Test")

            mocked_file.assert_called_once_with("test_output.mp3", "wb")
            mocked_file().write.assert_called_once_with(audio_bytes)

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_extracts_word_timings(self, mock_elevenlabs_client):
        """Test that word timings are extracted from alignment data."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance

        # "Hi there" with character-level timing
        mock_response = MagicMock()
        mock_response.audio_base_64 = base64.b64encode(b"audio").decode()
        mock_response.alignment = MagicMock()
        mock_response.alignment.characters = list("Hi there")
        mock_response.alignment.character_start_times_seconds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        mock_response.alignment.character_end_times_seconds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        mock_client_instance.text_to_speech.convert_with_timestamps.return_value = mock_response

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()):
            service.text_to_speech("Hi there")

        assert len(service.word_timings) == 2
        assert service.word_timings[0].word == "Hi"
        assert service.word_timings[0].start_time == 0.0
        assert service.word_timings[0].end_time == 0.2  # End of 'i' (index 1)
        assert service.word_timings[1].word == "there"
        assert service.word_timings[1].start_time == 0.3  # Start of 't' (index 3)
        assert service.word_timings[1].end_time == 0.8  # End of 'e' (index 7)

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_handles_no_alignment(self, mock_elevenlabs_client):
        """Test that word_timings is empty when no alignment data."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.audio_base_64 = base64.b64encode(b"audio").decode()
        mock_response.alignment = None
        mock_client_instance.text_to_speech.convert_with_timestamps.return_value = mock_response

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_id="test-model-id",
            output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()):
            service.text_to_speech("Test")

        assert service.word_timings == []

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_raises_on_error(self, mock_elevenlabs_client):
        """Test that text_to_speech raises TTSServiceError on failure."""
        from app.core.exceptions import TTSServiceError

        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert_with_timestamps.side_effect = Exception("API Error")

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
