from app.api.v1.endpoints.conversion import router as conversion_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.formats import router as formats_router
from app.api.v1.endpoints.smart import router as smart_router

__all__ = [
    "conversion_router",
    "health_router",
    "formats_router",
    "smart_router"
]
