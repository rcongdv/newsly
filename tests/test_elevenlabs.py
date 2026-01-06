"""Tests for the ElevenLabsService in app.integrations.tts.elevenlabs."""

import pytest
from unittest.mock import MagicMock, patch, mock_open, call

from app.integrations.tts.elevenlabs import ElevenLabsService, create_elevenlabs_service


class TestElevenLabsService:
    """Tests for the ElevenLabsService class."""

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_init_success(self, mock_elevenlabs_client):
        """Test successful initialization of ElevenLabsService."""
        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["test-model-id"],
            base_output_path="test_output.mp3",
        )

        mock_elevenlabs_client.assert_called_once_with(api_key="test-api-key", timeout=300.0)
        assert service._voice_id == "test-voice-id"
        assert service._model_ids == ["test-model-id"]
        assert service._base_output_path == "test_output.mp3"

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_init_multiple_models(self, mock_elevenlabs_client):
        """Test initialization with multiple model IDs."""
        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["model1", "model2", "model3"],
            base_output_path="output.mp3",
        )

        assert service._model_ids == ["model1", "model2", "model3"]

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_generate_output_path(self, mock_elevenlabs_client):
        """Test output path generation includes model ID."""
        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["model1"],
            base_output_path="output.mp3",
        )

        path = service._generate_output_path("eleven_multilingual_v2")
        assert path == "output_eleven_multilingual_v2.mp3"

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_calls_api(self, mock_elevenlabs_client):
        """Test that text_to_speech calls the ElevenLabs API with correct parameters."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert.return_value = iter([b"audio", b"data"])

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["test-model-id"],
            base_output_path="test_output.mp3",
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
            model_ids=["test-model-id"],
            base_output_path="test_output.mp3",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            service.text_to_speech("Hello world")

            mocked_file.assert_called_once_with("test_output_test-model-id.mp3", "wb")
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
            model_ids=["test-model-id"],
            base_output_path="test_output.mp3",
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
            model_ids=["test-model-id"],
            base_output_path="test_output.mp3",
        )

        with pytest.raises(TTSServiceError):
            service.text_to_speech("Test")

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_text_to_speech_multiple_models(self, mock_elevenlabs_client):
        """Test TTS generates file for each model."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert.return_value = iter([b"audio"])

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["model1", "model2"],
            base_output_path="output.mp3",
        )

        with patch("builtins.open", mock_open()):
            service.text_to_speech("Test text")

        assert len(service.output_paths) == 2
        assert service.output_paths == ["output_model1.mp3", "output_model2.mp3"]
        assert mock_client_instance.text_to_speech.convert.call_count == 2

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_output_path_returns_first(self, mock_elevenlabs_client):
        """Test output_path property returns first model's path."""
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        mock_client_instance.text_to_speech.convert.return_value = iter([b"audio"])

        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["model1", "model2"],
            base_output_path="output.mp3",
        )

        with patch("builtins.open", mock_open()):
            service.text_to_speech("Test")

        assert service.output_path == "output_model1.mp3"

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_output_path_before_generation(self, mock_elevenlabs_client):
        """Test output_path returns expected path before text_to_speech is called."""
        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["model1"],
            base_output_path="output.mp3",
        )

        assert service.output_path == "output_model1.mp3"

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_output_paths_empty_before_generation(self, mock_elevenlabs_client):
        """Test output_paths is empty before text_to_speech is called."""
        service = ElevenLabsService(
            api_key="test-api-key",
            voice_id="test-voice-id",
            model_ids=["model1", "model2"],
            base_output_path="output.mp3",
        )

        assert service.output_paths == []


class TestCreateElevenLabsService:
    """Tests for the create_elevenlabs_service factory function."""

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_create_elevenlabs_service_from_settings(self, mock_elevenlabs_client):
        """Test that create_elevenlabs_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.elevenlabs_api_key = "settings-api-key"
        mock_settings.elevenlabs_voice_id = "settings-voice-id"
        mock_settings.elevenlabs_model_id_list = ["settings-model-id"]
        mock_settings.tts_output_path = "settings_output.mp3"
        mock_settings.elevenlabs_timeout = 300.0

        service = create_elevenlabs_service(mock_settings)

        assert isinstance(service, ElevenLabsService)
        mock_elevenlabs_client.assert_called_once_with(api_key="settings-api-key", timeout=300.0)
        assert service._model_ids == ["settings-model-id"]

    @patch("app.integrations.tts.elevenlabs.ElevenLabs")
    def test_create_elevenlabs_service_multiple_models(self, mock_elevenlabs_client):
        """Test factory creates service with multiple models from settings."""
        mock_settings = MagicMock()
        mock_settings.elevenlabs_api_key = "api-key"
        mock_settings.elevenlabs_voice_id = "voice-id"
        mock_settings.elevenlabs_model_id_list = ["model1", "model2", "model3"]
        mock_settings.tts_output_path = "output.mp3"
        mock_settings.elevenlabs_timeout = 300.0

        service = create_elevenlabs_service(mock_settings)

        assert service._model_ids == ["model1", "model2", "model3"]
