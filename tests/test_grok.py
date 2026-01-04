"""Tests for the GrokService in app.integrations.ai.grok."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.integrations.ai.grok import GrokService, create_grok_service


class TestGrokService:
    """Tests for the GrokService class."""

    @patch("app.integrations.ai.grok.Client")
    def test_init_success(self, mock_client):
        """Test successful initialization of GrokService."""
        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service = GrokService(
            api_key="test-api-key",
            model="test-model",
            language="en",
        )

        mock_client.assert_called_once_with(api_key="test-api-key")
        assert service._model == "test-model"
        assert service._api_key == "test-api-key"

    def test_init_missing_api_key(self):
        """Test that initialization raises ValueError when API key is missing."""
        with pytest.raises(ValueError, match="Missing required GROK_API_KEY"):
            GrokService(api_key="", model="test-model")

    def test_init_none_api_key(self):
        """Test that initialization raises ValueError when API key is None."""
        with pytest.raises(ValueError, match="Missing required GROK_API_KEY"):
            GrokService(api_key=None, model="test-model")

    @patch("app.integrations.ai.grok.Client")
    def test_summarize_creates_new_chat_per_request(self, mock_client):
        """Test that summarize creates a fresh chat instance per request."""
        mock_chat = MagicMock()
        mock_chat.sample.return_value = MagicMock(content="Summary response")
        mock_client.return_value.chat.create.return_value = mock_chat

        service = GrokService(
            api_key="test-api-key",
            model="test-model",
        )

        # Call summarize twice
        service.summarize("First content")
        service.summarize("Second content")

        # chat.create should be called twice (once per summarize call)
        # This verifies the concurrency fix - new chat per request
        assert mock_client.return_value.chat.create.call_count == 2

    @patch("app.integrations.ai.grok.Client")
    def test_summarize_returns_content(self, mock_client):
        """Test that summarize returns the response content."""
        mock_chat = MagicMock()
        mock_chat.sample.return_value = MagicMock(content="Test summary")
        mock_client.return_value.chat.create.return_value = mock_chat

        service = GrokService(
            api_key="test-api-key",
            model="test-model",
        )

        result = service.summarize("Test content")

        assert result == "Test summary"
        mock_chat.append.assert_called_once()
        mock_chat.sample.assert_called_once()

    @patch("app.integrations.ai.grok.Client")
    def test_prompt_calls_summarize(self, mock_client):
        """Test that prompt method calls summarize for backward compatibility."""
        mock_chat = MagicMock()
        mock_chat.sample.return_value = MagicMock(content="Response")
        mock_client.return_value.chat.create.return_value = mock_chat

        service = GrokService(
            api_key="test-api-key",
            model="test-model",
        )

        result = service.prompt("Test prompt")

        assert result == "Response"

    @patch("app.integrations.ai.grok.Client")
    def test_chinese_language_appends_to_system_prompt(self, mock_client):
        """Test that Chinese language setting modifies system prompt."""
        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service = GrokService(
            api_key="test-api-key",
            model="test-model",
            language="ch",
        )

        assert "Mandarin Chinese" in service._system_prompt

    @patch("app.integrations.ai.grok.Client")
    def test_custom_system_prompt_path(self, mock_client, tmp_path):
        """Test that custom system prompt path is used."""
        # Create a temporary prompt file
        prompt_file = tmp_path / "custom_prompt.md"
        prompt_file.write_text("Custom system prompt")

        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service = GrokService(
            api_key="test-api-key",
            model="test-model",
            system_prompt_path=prompt_file,
        )

        assert service._system_prompt == "Custom system prompt"


class TestCreateGrokService:
    """Tests for the create_grok_service factory function."""

    @patch("app.integrations.ai.grok.Client")
    def test_create_grok_service_from_settings(self, mock_client):
        """Test that create_grok_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.grok_api_key = "settings-api-key"
        mock_settings.grok_model = "settings-model"
        mock_settings.tts_language = "en"

        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service = create_grok_service(mock_settings)

        assert isinstance(service, GrokService)
        mock_client.assert_called_once_with(api_key="settings-api-key")
