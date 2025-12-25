from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Google Auth
    google_auth_client_id: str
    google_auth_client_secret: str
    google_auth_refresh_token: str
    gmail_pubsub_topic_name: str

    # Grok AI
    grok_api_key: str
    grok_model: str = "grok-3-mini"

    # ElevenLabs TTS
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model_id: str = "eleven_multilingual_v2"

    # PyTTS
    pytts_voice_rate: int = 125
    pytts_volume: float = 1.0
    pytts_voice_id: str = "0"

    # TTS General
    tts_provider: str = "pytts"
    tts_output_format: str = "mp3"
    tts_output_file: str = "output"

    # Database
    database_url: str

    # Fly.io
    fly_app: bool = False

    # Other
    time_frames: dict = {
        "morning": ("00:00:00", "6:45:00"),
        "afternoon": ("06:45:00", "13:30:00"),
    }
    time_format: str = "%H:%M:%S"

    @property
    def tts_output_path(self) -> str:
        return f"{self.tts_output_file}.{self.tts_output_format}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
