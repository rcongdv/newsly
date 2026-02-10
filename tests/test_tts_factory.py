"""Tests for the TTSFactory in app.integrations.tts.factory."""

import pytest
from unittest.mock import MagicMock, patch

from app.integrations.tts.factory import TTSFactory
from app.integrations.tts.elevenlabs import ElevenLabsService
from app.integrations.tts.pocket_tts import PocketTTSService


class TestTTSFactory:
    """Tests for the TTSFactory class."""

    @patch("app.integrations.tts.factory.create_elevenlabs_service")
    def test_create_elevenlabs_service(self, mock_create_elevenlabs):
        """Test that TTSFactory creates ElevenLabsService for 'elevenlabs' provider."""
        mock_service = MagicMock(spec=ElevenLabsService)
        mock_create_elevenlabs.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "elevenlabs"

        result = TTSFactory.create(mock_settings)

        mock_create_elevenlabs.assert_called_once_with(mock_settings)
        assert result is mock_service

    @patch("app.integrations.tts.factory.create_pocket_tts_service")
    def test_create_pocket_tts_service(self, mock_create_pocket):
        """Test that TTSFactory creates PocketTTSService for 'pocket_tts' provider."""
        mock_service = MagicMock(spec=PocketTTSService)
        mock_create_pocket.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "pocket_tts"

        result = TTSFactory.create(mock_settings)

        mock_create_pocket.assert_called_once_with(mock_settings)
        assert result is mock_service

    def test_create_unknown_provider_raises_value_error(self):
        """Test that TTSFactory raises ValueError for unknown provider."""
        mock_settings = MagicMock()
        mock_settings.tts_provider = "unknown_provider"

        with pytest.raises(ValueError, match="Unknown TTS provider: unknown_provider"):
            TTSFactory.create(mock_settings)

    @patch("app.integrations.tts.factory.create_elevenlabs_service")
    def test_create_case_insensitive(self, mock_create_elevenlabs):
        """Test that provider matching is case-insensitive."""
        mock_service = MagicMock(spec=ElevenLabsService)
        mock_create_elevenlabs.return_value = mock_service
        mock_settings = MagicMock()
        mock_settings.tts_provider = "ElevenLabs"

        result = TTSFactory.create(mock_settings)

        mock_create_elevenlabs.assert_called_once_with(mock_settings)
        assert result is mock_service
