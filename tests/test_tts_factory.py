import pytest
from unittest.mock import MagicMock, patch
import app.tts.tts as tts_module


class TestTTSServiceFactory:

    @patch("app.tts.tts.get_elevenlabs_service")
    def test_get_service_returns_elevenlabs(self, mock_get_elevenlabs):
        """Test that get_service returns ElevenLabs service when specified."""
        mock_service = MagicMock()
        mock_get_elevenlabs.return_value = mock_service

        result = tts_module.TTSServiceFactory.get_service("elevenlabs")

        mock_get_elevenlabs.assert_called_once()
        assert result is mock_service

    @patch("app.tts.tts.get_pytts_service")
    def test_get_service_returns_pytts_for_other(self, mock_get_pytts):
        """Test that get_service returns PyTTS service for any other value."""
        mock_service = MagicMock()
        mock_get_pytts.return_value = mock_service

        result = tts_module.TTSServiceFactory.get_service("pytts")

        mock_get_pytts.assert_called_once()
        assert result is mock_service

    @patch("app.tts.tts.get_pytts_service")
    def test_get_service_returns_pytts_as_default(self, mock_get_pytts):
        """Test that get_service returns PyTTS service as default."""
        mock_service = MagicMock()
        mock_get_pytts.return_value = mock_service

        result = tts_module.TTSServiceFactory.get_service(None)

        mock_get_pytts.assert_called_once()
        assert result is mock_service

    @patch("app.tts.tts.get_pytts_service")
    def test_get_service_returns_pytts_for_unknown(self, mock_get_pytts):
        """Test that get_service returns PyTTS service for unknown provider."""
        mock_service = MagicMock()
        mock_get_pytts.return_value = mock_service

        result = tts_module.TTSServiceFactory.get_service("unknown_provider")

        mock_get_pytts.assert_called_once()
        assert result is mock_service

    @patch("app.tts.tts.os.getenv")
    @patch("app.tts.tts.TTSServiceFactory.get_service")
    def test_text_to_speech_uses_env_provider(self, mock_get_service, mock_getenv):
        """Test that text_to_speech reads TTS_PROVIDER from environment."""
        mock_getenv.return_value = "elevenlabs"
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        tts_module.TTSServiceFactory.text_to_speech("Hello")

        mock_getenv.assert_called_once_with("TTS_PROVIDER")
        mock_get_service.assert_called_once_with("elevenlabs")

    @patch("app.tts.tts.os.getenv")
    @patch("app.tts.tts.TTSServiceFactory.get_service")
    def test_text_to_speech_calls_service(self, mock_get_service, mock_getenv):
        """Test that text_to_speech calls the service's text_to_speech method."""
        mock_getenv.return_value = "pytts"
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        tts_module.TTSServiceFactory.text_to_speech("Hello world")

        mock_service.text_to_speech.assert_called_once_with("Hello world")

    @patch("app.tts.tts.os.getenv")
    @patch("app.tts.tts.TTSServiceFactory.get_service")
    def test_text_to_speech_returns_service_result(self, mock_get_service, mock_getenv):
        """Test that text_to_speech returns the result from the service."""
        mock_getenv.return_value = "elevenlabs"
        mock_service = MagicMock()
        mock_service.text_to_speech.return_value = b"audio_bytes"
        mock_get_service.return_value = mock_service

        result = tts_module.TTSServiceFactory.text_to_speech("Test")

        assert result == b"audio_bytes"

    @patch("app.tts.tts.os.getenv")
    @patch("app.tts.tts.get_elevenlabs_service")
    def test_text_to_speech_with_elevenlabs_integration(self, mock_get_elevenlabs, mock_getenv):
        """Test text_to_speech integration with ElevenLabs service."""
        mock_getenv.return_value = "elevenlabs"
        mock_service = MagicMock()
        mock_get_elevenlabs.return_value = mock_service

        tts_module.TTSServiceFactory.text_to_speech("Integration test")

        mock_get_elevenlabs.assert_called_once()
        mock_service.text_to_speech.assert_called_once_with("Integration test")

    @patch("app.tts.tts.os.getenv")
    @patch("app.tts.tts.get_pytts_service")
    def test_text_to_speech_with_pytts_integration(self, mock_get_pytts, mock_getenv):
        """Test text_to_speech integration with PyTTS service."""
        mock_getenv.return_value = "pytts"
        mock_service = MagicMock()
        mock_get_pytts.return_value = mock_service

        tts_module.TTSServiceFactory.text_to_speech("Integration test")

        mock_get_pytts.assert_called_once()
        mock_service.text_to_speech.assert_called_once_with("Integration test")
