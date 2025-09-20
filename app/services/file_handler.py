# document_processor/app/services/file_handler.py
from fastapi import UploadFile
import os
import shutil
from pathlib import Path
from app.core.config import settings

async def save_upload_file(file: UploadFile, task_id: str) -> str:
    """
    Save uploaded file to the filesystem
    """
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create task-specific directory
    task_dir = upload_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = task_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return str(file_path)

def create_output_directory(task_id: str) -> str:
    """
    Create output directory for processed files
    """
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    task_output_dir = output_dir / task_id
    task_output_dir.mkdir(parents=True, exist_ok=True)
    
    return str(task_output_dir)

def cleanup_files(task_id: str):
    """
    Clean up temporary files after processing
    """
    # Remove uploaded files
    upload_task_dir = Path(settings.UPLOAD_DIR) / task_id
    if upload_task_dir.exists():
        shutil.rmtree(upload_task_dir)
    
    # Note: We might want to keep output files for download
    # This is a design decision based on requirements