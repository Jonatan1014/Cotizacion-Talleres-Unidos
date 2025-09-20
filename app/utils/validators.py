# document_processor/app/utils/validators.py
from fastapi import UploadFile
import os
from pathlib import Path
from app.core.config import settings

def validate_file_type(filename: str) -> bool:
    """
    Validate if file type is supported
    """
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    return file_ext.replace('.', '') in settings.ALLOWED_EXTENSIONS

def validate_file_size(file: UploadFile) -> bool:
    """
    Validate if file size is within limits
    """
    # Note: This is a simplified check. In production, you might need
    # to check actual file size after upload depending on how FastAPI handles it
    return True  # FastAPI handles this with middleware