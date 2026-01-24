from functools import lru_cache

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

    # ============ API Security ============
    api_key: str  # Required for authenticated endpoints
    rate_limit_per_minute: int = 30  # Max requests per minute per IP

    # ============ Pub/Sub OIDC Authentication ============
    pubsub_service_account_email: str
    pubsub_audience: str

    # ============ Timezone & Recipients ============
    timezone: str = "America/Los_Angeles"
    default_recipient: EmailStr = "richardcong635@gmail.com"

    # ============ Google Auth ============
    google_auth_client_id: str
    google_auth_client_secret: str
    google_auth_refresh_token: str
    gmail_pubsub_topic_name: str

    # ============ AI Provider Selection ============
    ai_provider: str = "grok"  # "grok" or "gemini"

    # ============ Grok AI ============
    grok_api_key: str = ""
    grok_model: str = "grok-3-mini"

    # ============ Gemini AI ============
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ============ TTS (ElevenLabs) ============
    tts_output_format: str = "mp3"
    tts_output_file: str = "output"
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model_id: str = "eleven_flash_v2_5"

    # ============ Video Generation ============
    video_enabled: bool = True
    video_output_format: str = "mp4"
    video_output_file: str = "output"
    video_background_color: str = "#1a1a2e"
    video_background_image: str | None = None
    video_width: int = 720
    video_height: int = 720

    # ============ Subtitles ============
    subtitle_font_size: int = 40
    subtitle_font_color: str = "white"
    subtitle_max_chars_per_line: int = 45

    # ============ Database ============
    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # ============ Time Frames ============
    time_frames: dict = {
        "morning": ("00:00:00", "06:00:00"),
        "afternoon": ("06:00:00", "13:30:00"),
        "weekend": ("00:00:00", "09:00:00"),
    }
    time_format: str = "%H:%M:%S"

    # ============ Email Filtering ============
    email_whitelist: str = ""

    @property
    def tts_output_path(self) -> str:
        return f"{self.tts_output_file}.{self.tts_output_format}"

    @property
    def video_output_path(self) -> str:
        return f"{self.video_output_file}.{self.video_output_format}"

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
