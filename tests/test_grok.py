import pytest
from unittest.mock import MagicMock, patch
import app.ai.grok as grok_module


class TestGrok:

    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Grok.API_KEY", "test-api-key")
    @patch("app.ai.grok.Grok.MODEL", "test-model")
    @patch("app.ai.grok.Grok.SYSTEM_PROMPT", "test-prompt")
    def test_init_success(self, mock_client):
        """Test successful initialization of Grok class."""
        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        grok = grok_module.Grok()

        mock_client.assert_called_once_with(api_key="test-api-key")
        mock_client.return_value.chat.create.assert_called_once()
        assert grok.chat == mock_chat

    @patch.dict("os.environ", {"GROK_API_KEY": "", "GROK_MODEL": "test-model"}, clear=True)
    def test_init_missing_api_key(self):
        """Test that initialization raises ValueError when API key is missing."""
        with pytest.raises(ValueError, match="Missing required GROK_API_KEY"):
            grok_module.Grok()

    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Grok.API_KEY", "test-api-key")
    @patch("app.ai.grok.Grok.MODEL", "test-model")
    @patch("app.ai.grok.Grok.SYSTEM_PROMPT", "test-prompt")
    def test_prompt(self, mock_client):
        """Test the prompt method sends message and returns response."""
        mock_chat = MagicMock()
        mock_chat.sample.return_value = "Test response from Grok"
        mock_client.return_value.chat.create.return_value = mock_chat

        grok = grok_module.Grok()
        response = grok.prompt("Hello, Grok!")

        mock_chat.reset.assert_called_once()
        mock_chat.append.assert_called_once()
        mock_chat.sample.assert_called_once()
        assert response == "Test response from Grok"

    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Grok.API_KEY", "test-api-key")
    @patch("app.ai.grok.Grok.MODEL", "test-model")
    @patch("app.ai.grok.Grok.SYSTEM_PROMPT", "test-prompt")
    def test_prompt_resets_chat_before_each_call(self, mock_client):
        """Test that prompt resets chat state before each call."""
        mock_chat = MagicMock()
        mock_chat.sample.return_value = "Response"
        mock_client.return_value.chat.create.return_value = mock_chat

        grok = grok_module.Grok()
        grok.prompt("First prompt")
        grok.prompt("Second prompt")

        assert mock_chat.reset.call_count == 2


class TestGetGrokService:

    def setup_method(self):
        """Reset the singleton before each test."""
        grok_module.grok_service = None

    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Grok.API_KEY", "test-api-key")
    @patch("app.ai.grok.Grok.MODEL", "test-model")
    @patch("app.ai.grok.Grok.SYSTEM_PROMPT", "test-prompt")
    def test_get_grok_service_creates_instance(self, mock_client):
        """Test that get_grok_service creates a new Grok instance."""
        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service = grok_module.get_grok_service()

        assert service is not None
        assert isinstance(service, grok_module.Grok)

    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Grok.API_KEY", "test-api-key")
    @patch("app.ai.grok.Grok.MODEL", "test-model")
    @patch("app.ai.grok.Grok.SYSTEM_PROMPT", "test-prompt")
    def test_get_grok_service_returns_singleton(self, mock_client):
        """Test that get_grok_service returns the same instance on subsequent calls."""
        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service1 = grok_module.get_grok_service()
        service2 = grok_module.get_grok_service()

        assert service1 is service2
        mock_client.assert_called_once()
