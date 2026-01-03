"""Global exception handlers."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    NewslyException,
    EmailNotFoundError,
    AIServiceError,
    TTSServiceError,
    GmailServiceError,
)
from app.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


async def newsly_exception_handler(request: Request, exc: NewslyException):
    """Handle custom Newsly exceptions."""
    logger.error(f"NewslyException: {exc.message}", extra={"detail": exc.detail})

    status_code = 500
    if isinstance(exc, EmailNotFoundError):
        status_code = 404

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=exc.message,
            detail=exc.detail,
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {exc}")

    settings = get_settings()
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.debug else None,
        ).model_dump(),
    )
