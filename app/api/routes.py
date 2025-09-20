# document_processor/app/api/routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import os
from typing import Optional
import json

from app.api.models import DocumentUploadRequest, DocumentUploadResponse
from app.services.file_handler import save_upload_file
from app.services.document_processor import process_document
from app.core.config import settings
from app.utils.validators import validate_file_type, validate_file_size

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    webhook_url: str = Form(...),
    metadata: Optional[str] = Form(None)
):
    """
    Upload a document for processing
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
        
        # Validate file
        if not validate_file_type(file.filename):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        if not validate_file_size(file):
            raise HTTPException(status_code=400, detail="File size exceeds limit")
        
        # Save uploaded file
        file_path = await save_upload_file(file, task_id)
        
        # Process document in background
        background_tasks.add_task(
            process_document,
            task_id=task_id,
            file_path=file_path,
            original_filename=file.filename,
            webhook_url=webhook_url,
            metadata=parsed_metadata
        )
        
        return DocumentUploadResponse(
            task_id=task_id,
            message="Document uploaded successfully. Processing started.",
            status="processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/status/{task_id}")
async def get_processing_status(task_id: str):
    """
    Get the processing status of a document
    """
    # In a production environment, this would check a database or cache
    # For now, we'll return a placeholder response
    return {
        "task_id": task_id,
        "status": "This endpoint would return actual processing status in production",
        "message": "Implementation would require database/cache integration"
    }