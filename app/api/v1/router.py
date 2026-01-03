"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, email

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(email.router, prefix="/email", tags=["email"])
