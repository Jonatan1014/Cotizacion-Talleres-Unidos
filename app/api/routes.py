"""
Rutas FastAPI para API de Procesamiento de Documentos

Implementa todos los endpoints para carga, procesamiento, transformación y extracción de archivos.
Soporta cargas multipart/form-data y binarias.
"""

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Header
from fastapi.responses import FileResponse, Response
from typing import Optional
import mimetypes
import os
from pathlib import Path

from app.services.document_service import DocumentService
from app.models.schemas import (
    DocumentProcessResponse,
    ErrorResponse,
    ArchiveExtractionResponse
)
from app.config import settings

router = APIRouter()
document_service = DocumentService()


# ===== Endpoints de Procesamiento de Documentos =====

@router.post("/documents")
async def upload_and_process_document(document: UploadFile = File(...)):
    """
    Cargar documento (multipart) y procesar automáticamente.
    
    Acepta: archivos PDF, DOCX, XLSX, XLSM
    """
    content = await document.read()
    
    upload_result = document_service.upload_document(
        file_content=content,
        filename=document.filename
    )
    
    if not upload_result['success']:
        raise HTTPException(status_code=400, detail=upload_result['message'])
    
    process_result = await document_service.process_document(
        upload_result['document']['file_path']
    )
    
    if not process_result['success']:
        raise HTTPException(status_code=400, detail=f"Falló el procesamiento: {process_result['message']}")
    
    return {
        'success': True,
        'upload': upload_result['document'],
        'processing': {
            'processed_file': process_result['processed_file']
        },
        'message': 'Documento cargado y procesado automáticamente'
    }


@router.post("/documents/bin")
async def upload_binary_document(
    request: Request,
    x_filename: Optional[str] = Header(None, alias="X-Filename")
):
    """
    Cargar documento como binario (application/octet-stream) y procesar.
    
    Requiere encabezado X-Filename con el nombre del archivo.
    """
    content = await request.body()
    
    if not content:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos del documento")
    
    filename = x_filename or f'document_{os.urandom(8).hex()}.pdf'
    
    # Auto-detectar extensión si falta
    if not Path(filename).suffix:
        filename += '.pdf'
    
    if len(content) > settings.upload_max_size:
        raise HTTPException(status_code=400, detail=f"El tamaño del archivo excede el límite de {settings.upload_max_size // (1024*1024)}MB")
    
    file_ext = Path(filename).suffix.lower().lstrip('.')
    if file_ext not in settings.allowed_document_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Tipos permitidos: {', '.join(settings.allowed_document_types)}"
        )
    
    upload_result = document_service.upload_document(
        file_content=content,
        filename=filename
    )
    
    if not upload_result['success']:
        raise HTTPException(status_code=400, detail=upload_result['message'])
    
    process_result = await document_service.process_document(
        upload_result['document']['file_path']
    )
    
    if not process_result['success']:
        raise HTTPException(status_code=400, detail=f"Falló el procesamiento: {process_result['message']}")
    
    return {
        'success': True,
        'upload': upload_result['document'],
        'processing': {
            'processed_file': process_result['processed_file']
        },
        'message': 'Documento cargado y procesado automáticamente'
    }


# ===== Endpoints de Transformación (Devolver Archivo) =====

@router.post("/documents/transform")
async def transform_and_return_document(document: UploadFile = File(...)):
    """
    Cargar documento (multipart) y devolver archivo transformado.
    """
    content = await document.read()
    
    upload_result = document_service.upload_document(
        file_content=content,
        filename=document.filename
    )
    
    if not upload_result['success']:
        raise HTTPException(status_code=400, detail=upload_result['message'])
    
    process_result = await document_service.process_document(
        upload_result['document']['file_path']
    )
    
    if not process_result['success']:
        raise HTTPException(status_code=400, detail=f"Falló el procesamiento: {process_result['message']}")
    
    processed_file = process_result['processed_file']
    
    if not os.path.exists(processed_file):
        raise HTTPException(status_code=404, detail="Archivo procesado no encontrado")
    
    mime_type = mimetypes.guess_type(processed_file)[0] or 'application/octet-stream'
    filename = os.path.basename(processed_file)
    
    return FileResponse(
        path=processed_file,
        media_type=mime_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/documents/transform/bin")
async def transform_and_return_binary_document(
    request: Request,
    x_filename: Optional[str] = Header(None, alias="X-Filename")
):
    """
    Cargar documento como binario y devolver archivo transformado como binario.
    """
    content = await request.body()
    
    if not content:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos del documento")
    
    filename = x_filename or f'document_{os.urandom(8).hex()}.pdf'
    
    if not Path(filename).suffix:
        filename += '.pdf'
    
    if len(content) > settings.upload_max_size:
        raise HTTPException(status_code=400, detail=f"El tamaño del archivo excede el límite de {settings.upload_max_size // (1024*1024)}MB")
    
    file_ext = Path(filename).suffix.lower().lstrip('.')
    if file_ext not in settings.allowed_document_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Tipos permitidos: {', '.join(settings.allowed_document_types)}"
        )
    
    upload_result = document_service.upload_document(
        file_content=content,
        filename=filename
    )
    
    if not upload_result['success']:
        raise HTTPException(status_code=400, detail=upload_result['message'])
    
    process_result = await document_service.process_document(
        upload_result['document']['file_path']
    )
    
    if not process_result['success']:
        raise HTTPException(status_code=400, detail=f"Falló el procesamiento: {process_result['message']}")
    
    processed_file = process_result['processed_file']
    
    if not os.path.exists(processed_file):
        raise HTTPException(status_code=404, detail="Archivo procesado no encontrado")
    
    with open(processed_file, 'rb') as f:
        file_content = f.read()
    
    mime_type = mimetypes.guess_type(processed_file)[0] or 'application/octet-stream'
    file_name = os.path.basename(processed_file)
    
    return Response(
        content=file_content,
        media_type='application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'X-File-Name': file_name,
            'X-File-Type': mime_type
        }
    )


# ===== Endpoints de Extracción de Archivos =====

@router.post("/uploads-ziprar")
async def upload_archive_and_extract(archive: UploadFile = File(...)):
    """
    Cargar archivo ZIP o RAR (multipart) y extraer todos los archivos.
    
    Devuelve JSON con archivos extraídos y contenido codificado en base64.
    """
    content = await archive.read()
    
    # Obtener extensión del archivo
    ext = Path(archive.filename).suffix.lower().lstrip('.')
    if ext not in settings.allowed_archive_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Permitidos: {', '.join(settings.allowed_archive_types)}"
        )
    
    if len(content) > settings.archive_max_size:
        raise HTTPException(
            status_code=400,
            detail=f"El tamaño del archivo excede el límite de {settings.archive_max_size // (1024*1024)}MB"
        )
    
    import uuid
    # Preservar la extensión original en el nombre temporal
    temp_filename = f"archive_{uuid.uuid4().hex}.{ext}"
    temp_path = os.path.join(settings.upload_dir, temp_filename)
    
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    result = document_service.extract_archive(temp_path)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/uploads-ziprar/bin")
async def upload_binary_archive_and_extract(
    request: Request,
    x_filename: Optional[str] = Header(None, alias="X-Filename")
):
    """
    Cargar archivo ZIP o RAR como binario y extraer todos los archivos.
    """
    content = await request.body()
    
    if not content:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos del archivo")
    
    # Obtener extensión del archivo o usar .zip por defecto
    filename = x_filename or f'archive_{os.urandom(8).hex()}.zip'
    
    ext = Path(filename).suffix.lower().lstrip('.')
    if not ext or ext not in settings.allowed_archive_types:
        # Si no hay extensión o no es válida, intentar detectar por contenido
        # Los archivos RAR empiezan con "Rar!" (0x52 0x61 0x72 0x21)
        if content[:4] == b'Rar!':
            ext = 'rar'
        # Los archivos ZIP empiezan con "PK" (0x50 0x4B)
        elif content[:2] == b'PK':
            ext = 'zip'
        else:
            ext = 'zip'  # fallback
        filename = f'archive_{os.urandom(8).hex()}.{ext}'
    
    if len(content) > settings.archive_max_size:
        raise HTTPException(
            status_code=400,
            detail=f"El tamaño del archivo excede el límite de {settings.archive_max_size // (1024*1024)}MB"
        )
    
    temp_path = os.path.join(settings.upload_dir, filename)
    
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    result = document_service.extract_archive(temp_path)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


# ===== Endpoints Auxiliares =====

@router.get("/documents")
async def get_documents():
    """Obtener lista de todos los documentos cargados"""
    documents = document_service.get_all_documents()
    return {'documents': documents}
