"""
Pydantic Models and Schemas for API Request/Response
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ConversionCategory(str, Enum):
    """Categories of file conversions."""
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"


class ConversionStatus(str, Enum):
    """Status of a conversion job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileInfo(BaseModel):
    """Information about a file."""
    filename: str = Field(..., description="Name of the file")
    original_filename: str = Field(..., description="Original uploaded filename")
    size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    extension: str = Field(..., description="File extension")
    
    model_config = ConfigDict(from_attributes=True)


class ConversionRequest(BaseModel):
    """Request model for file conversion."""
    target_format: str = Field(
        ..., 
        description="Target format to convert to (e.g., 'png', 'pdf', 'mp3')",
        examples=["png", "pdf", "mp3"]
    )
    quality: Optional[int] = Field(
        default=85,
        ge=1,
        le=100,
        description="Quality for lossy formats (1-100)"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional conversion options specific to format"
    )


class ConversionResponse(BaseModel):
    """Response model for file conversion."""
    job_id: str = Field(..., description="Unique identifier for the conversion job")
    status: ConversionStatus = Field(..., description="Current status of the conversion")
    original_file: FileInfo = Field(..., description="Information about the original file")
    converted_file: Optional[FileInfo] = Field(None, description="Information about converted file")
    target_format: str = Field(..., description="Target format requested")
    download_url: Optional[str] = Field(None, description="URL to download the converted file")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    error_message: Optional[str] = Field(None, description="Error message if conversion failed")
    
    model_config = ConfigDict(from_attributes=True)


class ConversionJobStatus(BaseModel):
    """Status of a conversion job."""
    job_id: str
    status: ConversionStatus
    progress: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None


class SupportedFormats(BaseModel):
    """List of supported formats for conversion."""
    category: ConversionCategory
    input_formats: List[str]
    output_formats: List[str]
    description: str


class SupportedFormatsResponse(BaseModel):
    """Response containing all supported formats."""
    formats: List[SupportedFormats]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, bool] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchConversionRequest(BaseModel):
    """Request for batch file conversion."""
    target_format: str
    quality: Optional[int] = 85
    options: Optional[Dict[str, Any]] = None


class BatchConversionResponse(BaseModel):
    """Response for batch conversion."""
    batch_id: str
    total_files: int
    jobs: List[ConversionResponse]
    created_at: datetime = Field(default_factory=datetime.utcnow)
