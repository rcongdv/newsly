from app.core.config import Settings, get_settings
from app.core.exceptions import (
    NewslyException,
    EmailNotFoundError,
    EmailAlreadyExistsError,
    AIServiceError,
    TTSServiceError,
    GmailServiceError,
    ConfigurationError,
)
from app.core.dependencies import (
    SettingsDep,
    DBSessionDep,
    EmailRepoDep,
    GmailClientDep,
    AIServiceDep,
    TTSServiceDep,
    EmailProcessorDep,
    SummaryGeneratorDep,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Exceptions
    "NewslyException",
    "EmailNotFoundError",
    "EmailAlreadyExistsError",
    "AIServiceError",
    "TTSServiceError",
    "GmailServiceError",
    "ConfigurationError",
    # Dependencies
    "SettingsDep",
    "DBSessionDep",
    "EmailRepoDep",
    "GmailClientDep",
    "AIServiceDep",
    "TTSServiceDep",
    "EmailProcessorDep",
    "SummaryGeneratorDep",
]
