"""Tests for the GoogleTTSService in app.integrations.tts.google_tts."""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from app.integrations.tts.google_tts import GoogleTTSService, create_google_tts_service


class TestGoogleTTSService:
    """Tests for the GoogleTTSService class."""

    def test_init_with_mp3_format(self):
        """Test initialization with native MP3 format."""
        service = GoogleTTSService(
            output_path="test_output.mp3",
            language_code="en-US",
            voice_name="en-US-Neural2-A",
            speaking_rate=1.0,
            pitch=0.0,
        )

        assert service._output_path == "test_output.mp3"
        assert service.output_path == "test_output.mp3"
        assert service._language_code == "en-US"
        assert service._voice_name == "en-US-Neural2-A"
        assert service._speaking_rate == 1.0
        assert service._pitch == 0.0
        assert service._audio_encoding == "MP3"
        assert service._needs_conversion is False
        assert service._client is None  # Lazy initialization

    def test_init_with_wav_format(self):
        """Test initialization with WAV format."""
        service = GoogleTTSService(
            output_path="test_output.wav",
            language_code="en-US",
        )

        assert service._audio_encoding == "LINEAR16"
        assert service._needs_conversion is False

    def test_init_with_ogg_format(self):
        """Test initialization with OGG format."""
        service = GoogleTTSService(
            output_path="test_output.ogg",
            language_code="en-US",
        )

        assert service._audio_encoding == "OGG_OPUS"
        assert service._needs_conversion is False

    def test_init_with_unsupported_format_needs_conversion(self):
        """Test that unsupported format triggers conversion."""
        service = GoogleTTSService(
            output_path="test_output.aiff",
            language_code="en-US",
        )

        assert service._audio_encoding == "LINEAR16"  # Generate as WAV
        assert service._needs_conversion is True
        assert service._temp_wav_path == "test_output_temp.wav"

    def test_init_with_voice_gender(self):
        """Test initialization with voice gender."""
        service = GoogleTTSService(
            output_path="test_output.mp3",
            language_code="en-US",
            voice_gender="FEMALE",
        )

        assert service._voice_gender == "FEMALE"

    def test_init_with_credentials_path(self):
        """Test initialization with credentials path."""
        service = GoogleTTSService(
            output_path="test_output.mp3",
            language_code="en-US",
            credentials_path="/path/to/credentials.json",
        )

        assert service._credentials_path == "/path/to/credentials.json"

    @patch("app.integrations.tts.google_tts.GoogleTTSService._get_client")
    def test_text_to_speech_calls_api(self, mock_get_client):
        """Test that text_to_speech calls Google Cloud TTS API."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.audio_content = b"audio_data"

        # Create mock client
        mock_client = MagicMock()
        mock_client.synthesize_speech.return_value = mock_response
        mock_get_client.return_value = mock_client

        service = GoogleTTSService(
            output_path="test_output.mp3",
            language_code="en-US",
            voice_name="en-US-Neural2-A",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            # Mock the google.cloud.texttospeech imports
            with patch.dict("sys.modules", {"google.cloud": MagicMock(), "google.cloud.texttospeech": MagicMock()}):
                with patch("app.integrations.tts.google_tts.GoogleTTSService._get_client", return_value=mock_client):
                    # Need to reimport to get the patched module
                    mock_tts_module = MagicMock()
                    mock_tts_module.SynthesisInput.return_value = "mock_input"
                    mock_tts_module.VoiceSelectionParams.return_value = "mock_voice"
                    mock_tts_module.AudioConfig.return_value = "mock_config"
                    mock_tts_module.AudioEncoding.MP3 = "MP3"

                    with patch("google.cloud.texttospeech", mock_tts_module):
                        service._client = mock_client
                        service.text_to_speech("Hello world")

        mock_client.synthesize_speech.assert_called_once()

    @patch("app.integrations.tts.google_tts.GoogleTTSService._get_client")
    def test_text_to_speech_writes_to_file(self, mock_get_client):
        """Test that text_to_speech writes audio to file."""
        mock_response = MagicMock()
        mock_response.audio_content = b"audio_bytes_here"

        mock_client = MagicMock()
        mock_client.synthesize_speech.return_value = mock_response
        mock_get_client.return_value = mock_client

        service = GoogleTTSService(
            output_path="test_output.mp3",
            language_code="en-US",
        )

        with patch("builtins.open", mock_open()) as mocked_file:
            with patch.dict("sys.modules", {"google.cloud": MagicMock(), "google.cloud.texttospeech": MagicMock()}):
                mock_tts = MagicMock()
                mock_tts.SynthesisInput.return_value = MagicMock()
                mock_tts.VoiceSelectionParams.return_value = MagicMock()
                mock_tts.AudioConfig.return_value = MagicMock()
                mock_tts.AudioEncoding.MP3 = "MP3"
                mock_tts.SsmlVoiceGender.NEUTRAL = "NEUTRAL"

                with patch("google.cloud.texttospeech", mock_tts):
                    service._client = mock_client
                    service.text_to_speech("Test text")

                    mocked_file.assert_called_with("test_output.mp3", "wb")
                    mocked_file().write.assert_called_once_with(b"audio_bytes_here")

    @patch("app.integrations.tts.base.os.remove")
    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.google_tts.GoogleTTSService._get_client")
    def test_text_to_speech_converts_unsupported_format(
        self, mock_get_client, mock_audio_segment, mock_remove
    ):
        """Test that unsupported formats are converted."""
        mock_response = MagicMock()
        mock_response.audio_content = b"wav_audio"

        mock_client = MagicMock()
        mock_client.synthesize_speech.return_value = mock_response
        mock_get_client.return_value = mock_client

        mock_audio = MagicMock()
        mock_audio_segment.from_wav.return_value = mock_audio

        service = GoogleTTSService(
            output_path="test_output.aiff",
            language_code="en-US",
        )

        with patch("builtins.open", mock_open()):
            with patch.dict("sys.modules", {"google.cloud": MagicMock(), "google.cloud.texttospeech": MagicMock()}):
                mock_tts = MagicMock()
                mock_tts.SynthesisInput.return_value = MagicMock()
                mock_tts.VoiceSelectionParams.return_value = MagicMock()
                mock_tts.AudioConfig.return_value = MagicMock()
                mock_tts.AudioEncoding.LINEAR16 = "LINEAR16"
                mock_tts.SsmlVoiceGender.NEUTRAL = "NEUTRAL"

                with patch("google.cloud.texttospeech", mock_tts):
                    service._client = mock_client
                    service.text_to_speech("Test")

        # Should convert WAV to AIFF
        mock_audio_segment.from_wav.assert_called_once_with("test_output_temp.wav")
        mock_audio.export.assert_called_once_with("test_output.aiff", format="aiff")

        # Should clean up temp file
        mock_remove.assert_called_once_with("test_output_temp.wav")

    def test_get_client_raises_on_import_error(self):
        """Test that _get_client raises TTSServiceError when library not installed."""
        from app.core.exceptions import TTSServiceError

        service = GoogleTTSService(
            output_path="test_output.mp3",
            language_code="en-US",
        )

        with patch.dict("sys.modules", {"google.cloud": None, "google.cloud.texttospeech": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                with pytest.raises(TTSServiceError) as exc_info:
                    service._get_client()

                assert "not installed" in exc_info.value.message.lower()

    @patch("app.integrations.tts.google_tts.GoogleTTSService._get_client")
    def test_text_to_speech_raises_on_api_error(self, mock_get_client):
        """Test that text_to_speech raises TTSServiceError on API failure."""
        from app.core.exceptions import TTSServiceError

        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        service = GoogleTTSService(
            output_path="test_output.mp3",
            language_code="en-US",
        )

        with patch.dict("sys.modules", {"google.cloud": MagicMock(), "google.cloud.texttospeech": MagicMock()}):
            mock_tts = MagicMock()
            mock_tts.SynthesisInput.return_value = MagicMock()
            mock_tts.VoiceSelectionParams.return_value = MagicMock()
            mock_tts.AudioConfig.return_value = MagicMock()
            mock_tts.AudioEncoding.MP3 = "MP3"
            mock_tts.SsmlVoiceGender.NEUTRAL = "NEUTRAL"

            with patch("google.cloud.texttospeech", mock_tts):
                service._client = mock_client
                with pytest.raises(TTSServiceError):
                    service.text_to_speech("Test")

    @patch("app.integrations.tts.base.AudioSegment")
    @patch("app.integrations.tts.google_tts.GoogleTTSService._get_client")
    def test_text_to_speech_raises_on_conversion_error(self, mock_get_client, mock_audio_segment):
        """Test that text_to_speech raises TTSServiceError on conversion failure."""
        from app.core.exceptions import TTSServiceError

        mock_response = MagicMock()
        mock_response.audio_content = b"audio"

        mock_client = MagicMock()
        mock_client.synthesize_speech.return_value = mock_response
        mock_get_client.return_value = mock_client

        mock_audio_segment.from_wav.side_effect = Exception("Conversion error")

        service = GoogleTTSService(
            output_path="test_output.aiff",
            language_code="en-US",
        )

        with patch("builtins.open", mock_open()):
            with patch.dict("sys.modules", {"google.cloud": MagicMock(), "google.cloud.texttospeech": MagicMock()}):
                mock_tts = MagicMock()
                mock_tts.SynthesisInput.return_value = MagicMock()
                mock_tts.VoiceSelectionParams.return_value = MagicMock()
                mock_tts.AudioConfig.return_value = MagicMock()
                mock_tts.AudioEncoding.LINEAR16 = "LINEAR16"
                mock_tts.SsmlVoiceGender.NEUTRAL = "NEUTRAL"

                with patch("google.cloud.texttospeech", mock_tts):
                    service._client = mock_client
                    with pytest.raises(TTSServiceError):
                        service.text_to_speech("Test")


class TestCreateGoogleTTSService:
    """Tests for the create_google_tts_service factory function."""

    def test_create_google_tts_service_from_settings(self):
        """Test that create_google_tts_service creates service from settings."""
        mock_settings = MagicMock()
        mock_settings.tts_output_path = "output.mp3"
        mock_settings.google_tts_language_code = "en-US"
        mock_settings.google_tts_voice_name = "en-US-Neural2-A"
        mock_settings.google_tts_voice_gender = "FEMALE"
        mock_settings.google_tts_speaking_rate = 1.2
        mock_settings.google_tts_pitch = 2.0
        mock_settings.google_tts_credentials_path = "/path/to/creds.json"

        service = create_google_tts_service(mock_settings)

        assert isinstance(service, GoogleTTSService)
        assert service._output_path == "output.mp3"
        assert service._language_code == "en-US"
        assert service._voice_name == "en-US-Neural2-A"
        assert service._voice_gender == "FEMALE"
        assert service._speaking_rate == 1.2
        assert service._pitch == 2.0
        assert service._credentials_path == "/path/to/creds.json"

    def test_create_google_tts_service_with_defaults(self):
        """Test that create_google_tts_service handles default values."""
        mock_settings = MagicMock()
        mock_settings.tts_output_path = "output.mp3"
        mock_settings.google_tts_language_code = "en-GB"
        mock_settings.google_tts_voice_name = None
        mock_settings.google_tts_voice_gender = "NEUTRAL"
        mock_settings.google_tts_speaking_rate = 1.0
        mock_settings.google_tts_pitch = 0.0
        mock_settings.google_tts_credentials_path = None

        service = create_google_tts_service(mock_settings)

        assert isinstance(service, GoogleTTSService)
        assert service._voice_name is None
        assert service._credentials_path is None
        assert service._voice_gender == "NEUTRAL"
