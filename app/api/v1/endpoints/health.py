"""
Health Check Endpoints
"""
from datetime import datetime
import shutil
from fastapi import APIRouter

from app.config.settings import settings
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the API and its dependencies"
)
async def health_check() -> HealthResponse:
    """
    Perform health check on the API and its services.
    
    Returns:
        HealthResponse with status and service availability
    """
    # Check external dependencies
    services = {
        "api": True,
        "storage": settings.UPLOAD_DIR.exists() and settings.OUTPUT_DIR.exists(),
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "libreoffice": _check_libreoffice()
    }
    
    overall_status = "healthy" if all([services["api"], services["storage"]]) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        services=services
    )


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the API is ready to receive requests"
)
async def readiness_check():
    """Check if the API is ready."""
    return {"ready": True}


@router.get(
    "/live",
    summary="Liveness Check",
    description="Check if the API is alive"
)
async def liveness_check():
    """Check if the API is alive."""
    return {"alive": True}


def _check_libreoffice() -> bool:
    """Check if LibreOffice is available."""
    paths = ["libreoffice", "soffice"]
    return any(shutil.which(p) is not None for p in paths)
