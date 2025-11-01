"""
Modelos Pydantic para validación y serialización de solicitudes/respuestas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentInfo(BaseModel):
    """Modelo de metadatos del documento"""
    original_name: str
    file_path: str
    file_type: str
    file_size: int
    status: str = "uploaded"
    created_at: str
    updated_at: str


class UploadResponse(BaseModel):
    """Respuesta para carga de documento"""
    success: bool
    document: DocumentInfo
    message: str


class ProcessingResult(BaseModel):
    """Resultado del procesamiento de documento"""
    processed_file: str


class DocumentProcessResponse(BaseModel):
    """Respuesta para carga y procesamiento de documento"""
    success: bool
    upload: DocumentInfo
    processing: ProcessingResult
    message: str


class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    success: bool = False
    message: str


class ExtractedFileInfo(BaseModel):
    """Información sobre archivo extraído de archivo comprimido"""
    name: str
    path: str
    relative_path: str
    url: str
    size: int
    type: str
    extension: str
    content: Optional[str] = None  # contenido binario codificado en base64


class ArchiveExtractionResponse(BaseModel):
    """Respuesta para extracción de archivo comprimido"""
    success: bool
    archive_path: str
    extraction_dir: str
    extracted_count: int
    files: List[ExtractedFileInfo]
    message: str
