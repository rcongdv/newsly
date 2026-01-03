"""Common response schemas for the Newsly API."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
