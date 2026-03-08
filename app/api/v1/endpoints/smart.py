"""
Smart Conversion Endpoint - Auto-detección y conversión inteligente
"""
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY
import io

from app.services.smart_converter import smart_converter, DetectedFileType

router = APIRouter()

# Constants
ERROR_NO_FILENAME = "No se proporcionó nombre de archivo"


def _validate_file(file: UploadFile) -> None:
    """Validar que el archivo tenga nombre."""
    if not file.filename:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=ERROR_NO_FILENAME
        )


@router.post(
    "/process",
    summary="Procesar archivo automáticamente",
    description="""
    Endpoint de conversión inteligente que detecta automáticamente el tipo de archivo
    y aplica la conversión correspondiente:
    
    - **Word** (.doc, .docx, .odt, .rtf) → **PDF**
    - **Excel** (.xls, .xlsx, .ods, .csv) → **PDF**
    - **PDF** (1 página) → **JPG**
    - **PDF** (más de 1 página) → Se devuelve **sin modificar**
    
    El archivo convertido se devuelve directamente en la respuesta.
    """,
    responses={
        200: {
            "description": "Archivo procesado exitosamente",
            "content": {
                "application/pdf": {},
                "image/jpeg": {},
            }
        },
        400: {"description": "Archivo no válido o tipo no soportado"},
        422: {"description": "Error en la conversión"}
    }
)
async def smart_process_file(
    file: Annotated[UploadFile, File(description="Archivo a procesar (Word, Excel o PDF)")]
):
    """
    Procesar archivo automáticamente según su tipo.
    
    El sistema detecta el tipo de archivo y aplica la conversión apropiada:
    - Documentos Word → PDF
    - Hojas de Excel → PDF  
    - PDFs de 1 página → Imagen JPG
    
    Returns:
        El archivo convertido como respuesta binaria directa
    """
    _validate_file(file)
    
    # Procesar archivo
    result = await smart_converter.convert(
        file_content=file.file,
        filename=file.filename,
        content_type=file.content_type
    )
    
    if not result.success:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": result.error_message,
                "original_type": result.original_type.value if result.original_type else None,
                "metadata": result.metadata
            }
        )
    
    # Devolver archivo convertido directamente
    return Response(
        content=result.output_data,
        media_type=result.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.output_filename}"',
            "X-Original-Type": result.original_type.value,
            "X-Output-Format": result.output_format,
            "X-File-Size": str(result.file_size)
        }
    )


@router.post(
    "/process/stream",
    summary="Procesar archivo con streaming",
    description="Versión streaming para archivos grandes"
)
async def smart_process_file_stream(
    file: Annotated[UploadFile, File(description="Archivo a procesar")]
):
    """
    Versión streaming del procesamiento inteligente.
    Optimizado para archivos grandes.
    """
    _validate_file(file)
    
    result = await smart_converter.convert(
        file_content=file.file,
        filename=file.filename,
        content_type=file.content_type
    )
    
    if not result.success:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": result.error_message,
                "original_type": result.original_type.value if result.original_type else None,
                "metadata": result.metadata
            }
        )
    
    # Crear generador para streaming
    def iterfile():
        chunk_size = 8192
        buffer = io.BytesIO(result.output_data)
        while chunk := buffer.read(chunk_size):
            yield chunk
    
    return StreamingResponse(
        iterfile(),
        media_type=result.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.output_filename}"',
            "Content-Length": str(result.file_size),
            "X-Original-Type": result.original_type.value,
            "X-Output-Format": result.output_format
        }
    )


@router.post(
    "/detect",
    summary="Detectar tipo de archivo",
    description="Detecta el tipo de archivo sin convertirlo"
)
async def detect_file_type(
    file: Annotated[UploadFile, File(description="Archivo a detectar")]
):
    """
    Detectar el tipo de archivo y la conversión que se aplicaría.
    
    Returns:
        Información sobre el tipo detectado y la conversión aplicable
    """
    _validate_file(file)
    
    from app.services.smart_converter import FileTypeDetector
    
    detected_type = FileTypeDetector.detect(file.filename, file.content_type)
    
    # Determinar conversión aplicable
    conversion_map = {
        DetectedFileType.WORD: {"target": "pdf", "description": "Se convertirá a PDF"},
        DetectedFileType.EXCEL: {"target": "pdf", "description": "Se convertirá a PDF"},
        DetectedFileType.PDF: {
            "target": "jpg",
            "description": "Se convertirá a JPG si tiene 1 página, de lo contrario se devuelve sin modificar"
        },
        DetectedFileType.UNKNOWN: {"target": None, "description": "Tipo no soportado"}
    }
    
    conversion_info = conversion_map.get(detected_type, conversion_map[DetectedFileType.UNKNOWN])
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "detected_type": detected_type.value,
        "supported": detected_type != DetectedFileType.UNKNOWN,
        "conversion": conversion_info
    }


@router.get(
    "/supported-types",
    summary="Tipos soportados",
    description="Lista de tipos de archivo soportados y sus conversiones"
)
async def get_supported_types():
    """
    Obtener lista de tipos de archivo soportados y sus conversiones.
    """
    return {
        "supported_types": [
            {
                "type": "word",
                "extensions": [".doc", ".docx", ".odt", ".rtf"],
                "converts_to": "pdf",
                "description": "Documentos de texto"
            },
            {
                "type": "excel", 
                "extensions": [".xls", ".xlsx", ".ods", ".csv"],
                "converts_to": "pdf",
                "description": "Hojas de cálculo"
            },
            {
                "type": "pdf",
                "extensions": [".pdf"],
                "converts_to": "jpg",
                "condition": "Solo PDFs de 1 página se convierten a JPG",
                "fallback": "PDFs con más de 1 página se devuelven sin modificar",
                "description": "Documentos PDF"
            }
        ],
        "output_formats": ["pdf", "jpg"]
    }
