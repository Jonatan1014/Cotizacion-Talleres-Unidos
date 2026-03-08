"""
API v1 Router - Combines all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import conversion, health, formats, smart

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

api_router.include_router(
    conversion.router,
    prefix="/conversion",
    tags=["Conversion"]
)

api_router.include_router(
    formats.router,
    prefix="/formats",
    tags=["Formats"]
)

api_router.include_router(
    smart.router,
    prefix="/smart",
    tags=["Smart Conversion"]
)
