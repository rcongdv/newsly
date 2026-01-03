"""Health check endpoint."""

import logging

from fastapi import APIRouter

from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint."""
    logger.info("Health check requested")
    return HealthResponse(status="healthy")
