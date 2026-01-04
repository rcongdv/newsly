"""Tests for the TTSFactory in app.integrations.tts.factory."""

import pytest
from unittest.mock import MagicMock, patch

from app.integrations.tts.factory import TTSFactory
from app.integrations.tts.elevenlabs import ElevenLabsService
from app.integrations.tts.pytts import PyTTSService
from app.integrations.tts.piper import PiperService
from app.integrations.tts.google_tts import GoogleTTSService


class TestTTSFactory:
    """Tests for the TTSFactory class."""

    @patch("app.integrations.tts.factory.create_elevenlabs_service")
    def test_create_returns_elevenlabs(self, mock_create_elevenlabs):
        """Test that create returns ElevenLabs service when specified."""
        mock_service = MagicMock(spec=ElevenLabsService)
        mock_create_elevenlabs.return_value = mock_service
        mock_settings = MagicMock()

        result = TTSFactory.create("elevenlabs", mock_settings)

        mock_create_elevenlabs.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_pytts_service")
    def test_create_returns_pytts(self, mock_create_pytts):
        """Test that create returns PyTTS service when specified."""
        mock_service = MagicMock(spec=PyTTSService)
        mock_create_pytts.return_value = mock_service
        mock_settings = MagicMock()

        result = TTSFactory.create("pytts", mock_settings)

        mock_create_pytts.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_piper_service")
    def test_create_returns_piper(self, mock_create_piper):
        """Test that create returns Piper service when specified."""
        mock_service = MagicMock(spec=PiperService)
        mock_create_piper.return_value = mock_service
        mock_settings = MagicMock()

        result = TTSFactory.create("piper", mock_settings)

        mock_create_piper.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.coqui.create_coqui_service")
    def test_create_returns_coqui(self, mock_create_coqui):
        """Test that create returns Coqui service when specified."""
        mock_service = MagicMock()
        mock_create_coqui.return_value = mock_service
        mock_settings = MagicMock()

        result = TTSFactory.create("coqui", mock_settings)

        mock_create_coqui.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_google_tts_service")
    def test_create_returns_google(self, mock_create_google):
        """Test that create returns Google TTS service when specified."""
        mock_service = MagicMock(spec=GoogleTTSService)
        mock_create_google.return_value = mock_service
        mock_settings = MagicMock()

        result = TTSFactory.create("google", mock_settings)

        mock_create_google.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_pytts_service")
    def test_create_defaults_to_pytts(self, mock_create_pytts):
        """Test that create returns PyTTS service as default for unknown providers."""
        mock_service = MagicMock(spec=PyTTSService)
        mock_create_pytts.return_value = mock_service
        mock_settings = MagicMock()

        result = TTSFactory.create("unknown_provider", mock_settings)

        mock_create_pytts.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_elevenlabs_service")
    def test_create_from_settings_elevenlabs(self, mock_create_elevenlabs):
        """Test that create_from_settings reads provider from settings."""
        mock_service = MagicMock(spec=ElevenLabsService)
        mock_create_elevenlabs.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "elevenlabs"

        result = TTSFactory.create_from_settings(mock_settings)

        mock_create_elevenlabs.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_pytts_service")
    def test_create_from_settings_pytts(self, mock_create_pytts):
        """Test that create_from_settings works with pytts provider."""
        mock_service = MagicMock(spec=PyTTSService)
        mock_create_pytts.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "pytts"

        result = TTSFactory.create_from_settings(mock_settings)

        mock_create_pytts.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_piper_service")
    def test_create_from_settings_piper(self, mock_create_piper):
        """Test that create_from_settings works with piper provider."""
        mock_service = MagicMock(spec=PiperService)
        mock_create_piper.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "piper"

        result = TTSFactory.create_from_settings(mock_settings)

        mock_create_piper.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.coqui.create_coqui_service")
    def test_create_from_settings_coqui(self, mock_create_coqui):
        """Test that create_from_settings works with coqui provider."""
        mock_service = MagicMock()
        mock_create_coqui.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "coqui"

        result = TTSFactory.create_from_settings(mock_settings)

        mock_create_coqui.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_google_tts_service")
    def test_create_from_settings_google(self, mock_create_google):
        """Test that create_from_settings works with google provider."""
        mock_service = MagicMock(spec=GoogleTTSService)
        mock_create_google.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "google"

        result = TTSFactory.create_from_settings(mock_settings)

        mock_create_google.assert_called_once_with(mock_settings)
        assert result is mock_service
