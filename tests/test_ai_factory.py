"""Tests for the AIFactory in app.integrations.ai.factory."""

import pytest
from unittest.mock import MagicMock, patch

from app.integrations.ai.factory import AIFactory
from app.integrations.ai.grok import GrokService
from app.integrations.ai.gemini import GeminiService


class TestAIFactory:
    """Tests for the AIFactory class."""

    @patch("app.integrations.ai.factory.create_grok_service")
    def test_create_grok_provider(self, mock_create_grok):
        """Test that factory creates GrokService for 'grok' provider."""
        mock_settings = MagicMock()
        mock_settings.ai_provider = "grok"
        mock_grok_service = MagicMock(spec=GrokService)
        mock_create_grok.return_value = mock_grok_service

        service = AIFactory.create(mock_settings)

        mock_create_grok.assert_called_once_with(mock_settings)
        assert service == mock_grok_service

    @patch("app.integrations.ai.factory.create_gemini_service")
    def test_create_gemini_provider(self, mock_create_gemini):
        """Test that factory creates GeminiService for 'gemini' provider."""
        mock_settings = MagicMock()
        mock_settings.ai_provider = "gemini"
        mock_gemini_service = MagicMock(spec=GeminiService)
        mock_create_gemini.return_value = mock_gemini_service

        service = AIFactory.create(mock_settings)

        mock_create_gemini.assert_called_once_with(mock_settings)
        assert service == mock_gemini_service

    @patch("app.integrations.ai.factory.create_grok_service")
    def test_create_provider_case_insensitive(self, mock_create_grok):
        """Test that provider selection is case insensitive."""
        mock_settings = MagicMock()
        mock_grok_service = MagicMock(spec=GrokService)
        mock_create_grok.return_value = mock_grok_service

        # Test uppercase
        mock_settings.ai_provider = "GROK"
        AIFactory.create(mock_settings)
        mock_create_grok.assert_called()

        # Test mixed case
        mock_create_grok.reset_mock()
        mock_settings.ai_provider = "Grok"
        AIFactory.create(mock_settings)
        mock_create_grok.assert_called()

    @patch("app.integrations.ai.factory.create_gemini_service")
    def test_create_gemini_case_insensitive(self, mock_create_gemini):
        """Test that gemini provider selection is case insensitive."""
        mock_settings = MagicMock()
        mock_gemini_service = MagicMock(spec=GeminiService)
        mock_create_gemini.return_value = mock_gemini_service

        # Test uppercase
        mock_settings.ai_provider = "GEMINI"
        AIFactory.create(mock_settings)
        mock_create_gemini.assert_called()

        # Test mixed case
        mock_create_gemini.reset_mock()
        mock_settings.ai_provider = "Gemini"
        AIFactory.create(mock_settings)
        mock_create_gemini.assert_called()

    def test_create_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.ai_provider = "unknown"

        with pytest.raises(ValueError, match="Unknown AI provider: unknown"):
            AIFactory.create(mock_settings)

    def test_create_empty_provider_raises_error(self):
        """Test that empty provider raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.ai_provider = ""

        with pytest.raises(ValueError, match="Unknown AI provider"):
            AIFactory.create(mock_settings)
