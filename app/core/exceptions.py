"""
Custom Exceptions and Exception Handlers
"""
from datetime import datetime
from typing import Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_422_UNPROCESSABLE_ENTITY
)


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class FileNotFoundError(APIException):
    """Exception when a file is not found."""
    
    def __init__(self, filename: str):
        super().__init__(
            message=f"File not found: {filename}",
            status_code=HTTP_404_NOT_FOUND,
            detail={"filename": filename, "error": "File does not exist"}
        )


class InvalidFileFormatError(APIException):
    """Exception for unsupported file formats."""
    
    def __init__(self, format: str, supported_formats: list = None):
        super().__init__(
            message=f"Unsupported file format: {format}",
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "format": format,
                "supported_formats": supported_formats or [],
                "error": "File format is not supported"
            }
        )


class ConversionError(APIException):
    """Exception when file conversion fails."""
    
    def __init__(self, message: str, original_error: Optional[str] = None):
        super().__init__(
            message=f"Conversion failed: {message}",
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": message,
                "original_error": original_error
            }
        )


class FileTooLargeError(APIException):
    """Exception when file exceeds size limit."""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"File too large: {file_size} bytes (max: {max_size} bytes)",
            status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "file_size": file_size,
                "max_size": max_size,
                "error": "File exceeds maximum allowed size"
            }
        )


class UnsupportedConversionError(APIException):
    """Exception for unsupported conversion combinations."""
    
    def __init__(self, source_format: str, target_format: str):
        super().__init__(
            message=f"Cannot convert from {source_format} to {target_format}",
            status_code=HTTP_400_BAD_REQUEST,
            detail={
                "source_format": source_format,
                "target_format": target_format,
                "error": "This conversion is not supported"
            }
        )


def create_error_response(
    status_code: int,
    error: str,
    detail: Any
) -> JSONResponse:
    """Create a standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "detail": detail,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for the application."""
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return create_error_response(
            status_code=exc.status_code,
            error=exc.message,
            detail=exc.detail
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return create_error_response(
            status_code=exc.status_code,
            error=str(exc.detail),
            detail=exc.detail
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return create_error_response(
            status_code=HTTP_400_BAD_REQUEST,
            error="Invalid value",
            detail=str(exc)
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return create_error_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal server error",
            detail="An unexpected error occurred"
        )
