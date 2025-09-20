# document_processor/app/core/config.py
import os
from typing import List

class Settings:
    PROJECT_NAME: str = "Document Processing API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # File settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB default
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")
    ALLOWED_EXTENSIONS: List[str] = os.getenv(
        "ALLOWED_EXTENSIONS", 
        "pdf,docx,xlsx,xlsm"
    ).split(",")
    
    # Webhook settings
    WEBHOOK_TIMEOUT: int = int(os.getenv("WEBHOOK_TIMEOUT", 30))
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost,https://localhost"
    ).split(",")

settings = Settings()