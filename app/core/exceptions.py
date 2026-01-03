"""Custom exceptions for the Newsly application."""


class NewslyException(Exception):
    """Base exception for Newsly app."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)


class EmailNotFoundError(NewslyException):
    """Raised when email is not found."""

    pass


class EmailAlreadyExistsError(NewslyException):
    """Raised when attempting to create duplicate email."""

    pass


class AIServiceError(NewslyException):
    """Raised when AI service fails."""

    pass


class TTSServiceError(NewslyException):
    """Raised when TTS generation fails."""

    pass


class GmailServiceError(NewslyException):
    """Raised when Gmail API fails."""

    pass


class ConfigurationError(NewslyException):
    """Raised when configuration is invalid."""

    pass
