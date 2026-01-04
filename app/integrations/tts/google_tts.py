"""Google Cloud Text-to-Speech service implementation.

Uses Google Cloud's neural TTS voices including WaveNet and Neural2
for high-quality speech synthesis.
"""

import logging
import os
from typing import Literal

from app.core.config import Settings
from app.core.exceptions import TTSServiceError
from app.integrations.tts.base import BaseTTSService

logger = logging.getLogger(__name__)


class GoogleTTSService(BaseTTSService):
    """Google Cloud text-to-speech service.

    Supports Standard, WaveNet, Neural2, and Studio voices.
    Requires Google Cloud credentials (GOOGLE_APPLICATION_CREDENTIALS env var
    or explicit credentials file path).
    """

    # Google Cloud TTS supports these formats natively
    NATIVE_FORMATS = {"mp3", "wav", "ogg"}

    # Audio encoding mapping
    ENCODING_MAP = {
        "mp3": "MP3",
        "wav": "LINEAR16",
        "ogg": "OGG_OPUS",
    }

    def __init__(
        self,
        output_path: str,
        language_code: str = "en-US",
        voice_name: str | None = None,
        voice_gender: Literal["NEUTRAL", "MALE", "FEMALE"] = "NEUTRAL",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        credentials_path: str | None = None,
    ):
        self._language_code = language_code
        self._voice_name = voice_name
        self._voice_gender = voice_gender
        self._speaking_rate = speaking_rate
        self._pitch = pitch
        self._credentials_path = credentials_path
        self._client = None  # Lazy initialization

        # Initialize format conversion (uses parent's logic)
        self._init_format_conversion(output_path)

        # Override audio encoding for native formats
        if self._target_format in self.NATIVE_FORMATS:
            self._audio_encoding = self.ENCODING_MAP[self._target_format]
        else:
            self._audio_encoding = "LINEAR16"

    def _get_client(self):
        """Lazy initialization of Google Cloud TTS client."""
        if self._client is None:
            try:
                from google.cloud import texttospeech
            except ImportError:
                raise TTSServiceError(
                    "Google Cloud TTS library not installed",
                    detail="Install with: pip install google-cloud-texttospeech",
                )

            if self._credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._credentials_path

            logger.info("Initializing Google Cloud TTS client")
            self._client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud TTS client initialized")

        return self._client

    def text_to_speech(self, text: str) -> None:
        """Generate TTS audio with Google Cloud TTS."""
        logger.info("Generating TTS audio with Google Cloud TTS")
        try:
            from google.cloud import texttospeech

            client = self._get_client()

            synthesis_input = texttospeech.SynthesisInput(text=text)

            voice_params = {"language_code": self._language_code}
            if self._voice_name:
                voice_params["name"] = self._voice_name
            else:
                gender_enum = getattr(
                    texttospeech.SsmlVoiceGender,
                    self._voice_gender,
                    texttospeech.SsmlVoiceGender.NEUTRAL,
                )
                voice_params["ssml_gender"] = gender_enum

            voice = texttospeech.VoiceSelectionParams(**voice_params)

            audio_encoding = getattr(texttospeech.AudioEncoding, self._audio_encoding)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=audio_encoding,
                speaking_rate=self._speaking_rate,
                pitch=self._pitch,
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            # Write to temp path if conversion needed, otherwise direct to output
            output_file = self._get_wav_output_path() if self._needs_conversion else self._output_path
            with open(output_file, "wb") as f:
                f.write(response.audio_content)

            logger.info(f"Google Cloud TTS generated audio: {output_file}")
            self._convert_if_needed()
            logger.info(f"TTS audio saved to {self._output_path}")

        except Exception as e:
            logger.error(f"Google Cloud TTS error: {e}")
            raise TTSServiceError(
                "Failed to generate TTS audio with Google Cloud TTS",
                detail=str(e),
            ) from e


def create_google_tts_service(settings: Settings) -> GoogleTTSService:
    """Factory function to create GoogleTTSService from settings."""
    return GoogleTTSService(
        output_path=settings.tts_output_path,
        language_code=settings.google_tts_language_code,
        voice_name=settings.google_tts_voice_name,
        voice_gender=settings.google_tts_voice_gender,
        speaking_rate=settings.google_tts_speaking_rate,
        pitch=settings.google_tts_pitch,
        credentials_path=settings.google_tts_credentials_path,
    )
