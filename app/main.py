"""
Newsly FastAPI Application

A news summarization service that fetches emails, generates AI summaries,
and delivers them via email with TTS audio attachments.
"""

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import NewslyException
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.db import get_database
from app.integrations.gmail.client import create_gmail_client
from app.middleware import (
    RequestLoggingMiddleware,
    newsly_exception_handler,
    generic_exception_handler,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger().handlers[0].flush = sys.stdout.flush
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    logger.info("Starting up...")

    logger.info("Initializing database...")
    await get_database().init_db()
    logger.info("Database initialized.")

    logger.info("Setting up Gmail watch...")
    try:
        settings = get_settings()
        gmail_client = create_gmail_client(settings)
        gmail_client.watch()
        logger.info("Gmail watch established successfully.")
    except Exception as e:
        logger.error(f"Failed to set up Gmail watch: {e}")

    yield

    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    # Configure rate limiter and attach to app state
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Register exception handlers
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_exception_handler(NewslyException, newsly_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Include API routers
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
