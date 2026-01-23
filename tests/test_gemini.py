"""Tests for the GeminiService in app.integrations.ai.gemini."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.integrations.ai.gemini import GeminiService, create_gemini_service


class TestGeminiService:
    """Tests for the GeminiService class."""

    @patch("app.integrations.ai.gemini.genai")
    def test_init_success(self, mock_genai):
        """Test successful initialization of GeminiService."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        service = GeminiService(
            api_key="test-api-key",
            model="test-model",
            language="en",
        )

        mock_genai.Client.assert_called_once_with(api_key="test-api-key")
        assert service._model == "test-model"
        assert service._api_key == "test-api-key"

    def test_init_missing_api_key(self):
        """Test that initialization raises ValueError when API key is missing."""
        with pytest.raises(ValueError, match="Missing required GEMINI_API_KEY"):
            GeminiService(api_key="", model="test-model")

    def test_init_none_api_key(self):
        """Test that initialization raises ValueError when API key is None."""
        with pytest.raises(ValueError, match="Missing required GEMINI_API_KEY"):
            GeminiService(api_key=None, model="test-model")

    @patch("app.integrations.ai.gemini.types")
    @patch("app.integrations.ai.gemini.genai")
    def test_summarize_calls_generate_content(self, mock_genai, mock_types):
        """Test that summarize calls the client's generate_content method."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = MagicMock(text="Summary response")
        mock_genai.Client.return_value = mock_client
        mock_config = MagicMock()
        mock_types.GenerateContentConfig.return_value = mock_config

        service = GeminiService(
            api_key="test-api-key",
            model="test-model",
        )

        # Call summarize twice
        service.summarize("First content")
        service.summarize("Second content")

        # generate_content should be called twice
        assert mock_client.models.generate_content.call_count == 2

    @patch("app.integrations.ai.gemini.types")
    @patch("app.integrations.ai.gemini.genai")
    def test_summarize_returns_content(self, mock_genai, mock_types):
        """Test that summarize returns the response text."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = MagicMock(text="Test summary")
        mock_genai.Client.return_value = mock_client

        service = GeminiService(
            api_key="test-api-key",
            model="test-model",
        )

        result = service.summarize("Test content")

        assert result == "Test summary"

    @patch("app.integrations.ai.gemini.types")
    @patch("app.integrations.ai.gemini.genai")
    def test_prompt_calls_summarize(self, mock_genai, mock_types):
        """Test that prompt method calls summarize for backward compatibility."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = MagicMock(text="Response")
        mock_genai.Client.return_value = mock_client

        service = GeminiService(
            api_key="test-api-key",
            model="test-model",
        )

        result = service.prompt("Test prompt")

        assert result == "Response"

    @patch("app.integrations.ai.gemini.genai")
    def test_chinese_language_appends_to_system_prompt(self, mock_genai):
        """Test that Chinese language setting modifies system prompt."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        service = GeminiService(
            api_key="test-api-key",
            model="test-model",
            language="ch",
        )

        assert "Mandarin Chinese" in service._system_prompt

    @patch("app.integrations.ai.gemini.genai")
    def test_custom_system_prompt_path(self, mock_genai, tmp_path):
        """Test that custom system prompt path is used."""
        # Create a temporary prompt file
        prompt_file = tmp_path / "custom_prompt.md"
        prompt_file.write_text("Custom system prompt")

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        service = GeminiService(
            api_key="test-api-key",
            model="test-model",
            system_prompt_path=prompt_file,
        )

        assert service._system_prompt == "Custom system prompt"

    @patch("app.integrations.ai.gemini.types")
    @patch("app.integrations.ai.gemini.genai")
    def test_summarize_passes_system_instruction(self, mock_genai, mock_types):
        """Test that system prompt is passed via GenerateContentConfig."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = MagicMock(text="Summary")
        mock_genai.Client.return_value = mock_client
        mock_config = MagicMock()
        mock_types.GenerateContentConfig.return_value = mock_config

        service = GeminiService(
            api_key="test-api-key",
            model="gemini-2.0-flash",
        )

        service.summarize("Test content")

        # Verify GenerateContentConfig was called with system_instruction
        mock_types.GenerateContentConfig.assert_called_once()
        call_kwargs = mock_types.GenerateContentConfig.call_args[1]
        assert "system_instruction" in call_kwargs

        # Verify generate_content was called with correct params
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash",
            contents="Test content",
            config=mock_config,
        )


class TestCreateGeminiService:
    """Tests for the create_gemini_service factory function."""

    @patch("app.integrations.ai.gemini.genai")
    def test_create_gemini_service_from_settings(self, mock_genai):
        """Test that create_gemini_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.gemini_api_key = "settings-api-key"
        mock_settings.gemini_model = "settings-model"

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        service = create_gemini_service(mock_settings)

        assert isinstance(service, GeminiService)
        mock_genai.Client.assert_called_once_with(api_key="settings-api-key")
        assert service._model == "settings-model"
