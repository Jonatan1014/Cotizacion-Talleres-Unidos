"""
File Conversion API - Main Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.api.v1.router import api_router
from app.core.middleware import RequestLoggingMiddleware
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup: Create necessary directories
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown: Cleanup temporary files if needed
    # Add cleanup logic here if necessary


def create_application() -> FastAPI:
    """Application factory for creating FastAPI instance."""
    
    application = FastAPI(
        title=settings.APP_NAME,
        description="API REST para conversión de archivos. Soporta múltiples formatos de imagen, documento y audio.",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom Middleware
    application.add_middleware(RequestLoggingMiddleware)
    
    # Register exception handlers
    register_exception_handlers(application)
    
    # Include API routers
    application.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX
    )
    
    return application


app = create_application()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "File Conversion API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
