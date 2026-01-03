"""Request logging middleware."""

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request/response information."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} started",
        )

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"completed in {duration:.3f}s with status {response.status_code}",
        )

        response.headers["X-Request-ID"] = request_id
        return response
