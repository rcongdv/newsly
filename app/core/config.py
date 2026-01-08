from functools import lru_cache
from typing import Literal

from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ============ App Settings ============
    app_name: str = "Newsly"
    debug: bool = False
    log_level: str = "INFO"

    # ============ Timezone & Recipients ============
    timezone: str = "America/Los_Angeles"
    default_recipient: EmailStr = "richardcong635@gmail.com"

    # ============ Google Auth ============
    google_auth_client_id: str
    google_auth_client_secret: str
    google_auth_refresh_token: str
    gmail_pubsub_topic_name: str

    # ============ Grok AI ============
    grok_api_key: str
    grok_model: str = "grok-3-mini"

    # ============ TTS General ============
    tts_provider: Literal["pytts", "elevenlabs", "google"] = "pytts"
    tts_output_format: str = "mp3"
    tts_output_file: str = "output"
    tts_language: str = "en"

    # ============ ElevenLabs TTS ============
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model_id: str = "eleven_multilingual_v2"

    # ============ PyTTS ============
    pytts_voice_rate: int = 125
    pytts_volume: float = 1.0
    pytts_voice_id: str = "0"

    # ============ Google Cloud TTS ============
    google_tts_credentials_path: str | None = None  # Path to service account JSON
    google_tts_language_code: str = "en-US"
    google_tts_voice_name: str | None = None  # e.g., "en-US-Neural2-A"
    google_tts_voice_gender: Literal["NEUTRAL", "MALE", "FEMALE"] = "NEUTRAL"
    google_tts_speaking_rate: float = 1.0  # 0.25 to 4.0
    google_tts_pitch: float = 0.0  # -20.0 to 20.0 semitones

    # ============ Database ============
    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # ============ Time Frames ============
    time_frames: dict = {
        "morning": ("00:00:00", "06:00:00"),
        "afternoon": ("06:00:00", "13:30:00"),
    }
    time_format: str = "%H:%M:%S"

    # ============ Email Filtering ============
    email_whitelist: str = ""

    @property
    def tts_output_path(self) -> str:
        return f"{self.tts_output_file}.{self.tts_output_format}"

    @property
    def email_domain_whitelist_list(self) -> list[str]:
        if not self.email_whitelist:
            return []
        return [d.strip() for d in self.email_whitelist.split(",") if d.strip()]

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        from zoneinfo import ZoneInfo

        try:
            ZoneInfo(v)
            return v
        except Exception:
            raise ValueError(f"Invalid timezone: {v}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
