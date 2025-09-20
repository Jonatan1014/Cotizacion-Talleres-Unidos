# document_processor/app/api/models.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentUploadRequest(BaseModel):
    webhook_url: str
    metadata: Optional[dict] = None

class DocumentUploadResponse(BaseModel):
    task_id: str
    message: str
    status: str

class DocumentProcessRequest(BaseModel):
    task_id: str
    file_path: str
    original_filename: str
    webhook_url: str
    metadata: Optional[dict] = None

class WebhookPayload(BaseModel):
    task_id: str
    status: str  # success, failed
    original_filename: str
    converted_filename: Optional[str] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Optional[dict] = None
    timestamp: datetime

class DocumentConversionResponse(BaseModel):
    task_id: str
    original_filename: str
    converted_filename: str
    download_url: str
    processing_time: float
    metadata: Optional[dict] = None