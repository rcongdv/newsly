import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import app.ai.grok as grok_module


class TestGrok:

    @patch("app.ai.grok.system")
    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Path")
    @patch("app.ai.grok.get_settings")
    def test_init_success(self, mock_get_settings, mock_path, mock_client, mock_system):
        """Test successful initialization of Grok class."""
        mock_settings = MagicMock()
        mock_settings.grok_api_key = "test-api-key"
        mock_settings.grok_model = "test-model"
        mock_get_settings.return_value = mock_settings

        mock_prompt_path = MagicMock()
        mock_prompt_path.exists.return_value = True
        mock_prompt_path.read_text.return_value = "test-prompt"
        mock_path.return_value.__truediv__.return_value = mock_prompt_path

        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        grok = grok_module.Grok()

        mock_client.assert_called_once_with(api_key="test-api-key")
        mock_client.return_value.chat.create.assert_called_once()
        assert grok.chat == mock_chat

    @patch("app.ai.grok.get_settings")
    def test_init_missing_api_key(self, mock_get_settings):
        """Test that initialization raises ValueError when API key is missing."""
        mock_settings = MagicMock()
        mock_settings.grok_api_key = ""
        mock_settings.grok_model = "test-model"
        mock_get_settings.return_value = mock_settings

        with pytest.raises(ValueError, match="Missing required GROK_API_KEY"):
            grok_module.Grok()

    @patch("app.ai.grok.system")
    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Path")
    @patch("app.ai.grok.get_settings")
    def test_prompt(self, mock_get_settings, mock_path, mock_client, mock_system):
        """Test the prompt method sends message and returns response."""
        mock_settings = MagicMock()
        mock_settings.grok_api_key = "test-api-key"
        mock_settings.grok_model = "test-model"
        mock_get_settings.return_value = mock_settings

        mock_prompt_path = MagicMock()
        mock_prompt_path.exists.return_value = True
        mock_prompt_path.read_text.return_value = "test-prompt"
        mock_path.return_value.__truediv__.return_value = mock_prompt_path

        mock_chat = MagicMock()
        mock_chat.sample.return_value = "Test response from Grok"
        mock_client.return_value.chat.create.return_value = mock_chat

        grok = grok_module.Grok()
        response = grok.prompt("Hello, Grok!")

        mock_chat.append.assert_called_once()
        mock_chat.sample.assert_called_once()
        assert response == "Test response from Grok"

    @patch("app.ai.grok.system")
    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Path")
    @patch("app.ai.grok.get_settings")
    def test_prompt_appends_to_chat(self, mock_get_settings, mock_path, mock_client, mock_system):
        """Test that prompt appends messages to chat."""
        mock_settings = MagicMock()
        mock_settings.grok_api_key = "test-api-key"
        mock_settings.grok_model = "test-model"
        mock_get_settings.return_value = mock_settings

        mock_prompt_path = MagicMock()
        mock_prompt_path.exists.return_value = True
        mock_prompt_path.read_text.return_value = "test-prompt"
        mock_path.return_value.__truediv__.return_value = mock_prompt_path

        mock_chat = MagicMock()
        mock_chat.sample.return_value = "Response"
        mock_client.return_value.chat.create.return_value = mock_chat

        grok = grok_module.Grok()
        grok.prompt("First prompt")
        grok.prompt("Second prompt")

        assert mock_chat.append.call_count == 2


class TestGetGrokService:

    def setup_method(self):
        """Reset the singleton before each test."""
        grok_module.grok_service = None

    @patch("app.ai.grok.system")
    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Path")
    @patch("app.ai.grok.get_settings")
    def test_get_grok_service_creates_instance(self, mock_get_settings, mock_path, mock_client, mock_system):
        """Test that get_grok_service creates a new Grok instance."""
        mock_settings = MagicMock()
        mock_settings.grok_api_key = "test-api-key"
        mock_settings.grok_model = "test-model"
        mock_get_settings.return_value = mock_settings

        mock_prompt_path = MagicMock()
        mock_prompt_path.exists.return_value = True
        mock_prompt_path.read_text.return_value = "test-prompt"
        mock_path.return_value.__truediv__.return_value = mock_prompt_path

        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service = grok_module.get_grok_service()

        assert service is not None
        assert isinstance(service, grok_module.Grok)

    @patch("app.ai.grok.system")
    @patch("app.ai.grok.Client")
    @patch("app.ai.grok.Path")
    @patch("app.ai.grok.get_settings")
    def test_get_grok_service_returns_singleton(self, mock_get_settings, mock_path, mock_client, mock_system):
        """Test that get_grok_service returns the same instance on subsequent calls."""
        mock_settings = MagicMock()
        mock_settings.grok_api_key = "test-api-key"
        mock_settings.grok_model = "test-model"
        mock_get_settings.return_value = mock_settings

        mock_prompt_path = MagicMock()
        mock_prompt_path.exists.return_value = True
        mock_prompt_path.read_text.return_value = "test-prompt"
        mock_path.return_value.__truediv__.return_value = mock_prompt_path

        mock_chat = MagicMock()
        mock_client.return_value.chat.create.return_value = mock_chat

        service1 = grok_module.get_grok_service()
        service2 = grok_module.get_grok_service()

        assert service1 is service2
        mock_client.assert_called_once()
