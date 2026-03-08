"""
File Conversion Endpoints
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.status import HTTP_400_BAD_REQUEST

from app.models.schemas import ConversionResponse
from app.services.conversion_service import conversion_service
from app.services.converter_factory import ConverterFactory
from app.config.settings import settings

router = APIRouter()


@router.post(
    "/convert",
    response_model=ConversionResponse,
    summary="Convert File",
    description="Upload a file and convert it to the specified format"
)
async def convert_file(
    file: UploadFile = File(..., description="File to convert"),
    target_format: str = Form(..., description="Target format (e.g., png, pdf, mp3)"),
    quality: Optional[int] = Form(default=85, ge=1, le=100, description="Quality for lossy formats"),
    width: Optional[int] = Form(default=None, description="Resize width (images only)"),
    height: Optional[int] = Form(default=None, description="Resize height (images only)"),
    bitrate: Optional[str] = Form(default="192k", description="Audio bitrate (e.g., 128k, 192k, 320k)")
) -> ConversionResponse:
    """
    Convert an uploaded file to the specified format.
    
    Supports:
    - **Images**: jpg, png, gif, bmp, webp, tiff → jpg, png, gif, bmp, webp, tiff, pdf
    - **Documents**: pdf, docx, doc, xlsx, txt, html → pdf, docx, txt, html
    - **Audio**: mp3, wav, ogg, flac, aac, m4a → mp3, wav, ogg, flac, aac, m4a
    
    Args:
        file: The file to convert
        target_format: The format to convert to
        quality: Quality for lossy formats (1-100, default 85)
        width: Optional resize width (images only)
        height: Optional resize height (images only)
        bitrate: Audio bitrate (audio only, default 192k)
    
    Returns:
        ConversionResponse with download URL and conversion details
    """
    if not file.filename:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Build options
    options = {"quality": quality}
    
    if width or height:
        options["resize"] = {}
        if width:
            options["resize"]["width"] = width
        if height:
            options["resize"]["height"] = height
    
    if bitrate:
        options["bitrate"] = bitrate
    
    # Perform conversion
    result = await conversion_service.convert_file(
        file_content=file.file,
        filename=file.filename,
        target_format=target_format.lower().lstrip('.'),
        options=options
    )
    
    return result


@router.get(
    "/download/{job_id}",
    summary="Download Converted File",
    description="Download a converted file by its job ID"
)
async def download_converted_file(job_id: str):
    """
    Download a converted file.
    
    Args:
        job_id: The conversion job ID from the convert response
    
    Returns:
        The converted file as a download
    """
    file_path = conversion_service.get_converted_file_path(job_id)
    
    return FileResponse(
        path=file_path,
        filename=file_path.name.replace(f"{job_id}_", ""),
        media_type="application/octet-stream"
    )


@router.delete(
    "/cleanup/{job_id}",
    summary="Cleanup Job Files",
    description="Delete files associated with a conversion job"
)
async def cleanup_job(job_id: str):
    """
    Clean up files from a conversion job.
    
    Args:
        job_id: The conversion job ID
    
    Returns:
        Cleanup status
    """
    cleaned = conversion_service.cleanup_job_files(job_id)
    
    return {
        "job_id": job_id,
        "cleaned": cleaned,
        "message": "Job files cleaned successfully" if cleaned else "No files found for this job"
    }


@router.post(
    "/validate",
    summary="Validate Conversion",
    description="Check if a conversion from source to target format is supported"
)
async def validate_conversion(
    source_format: str = Form(..., description="Source file format"),
    target_format: str = Form(..., description="Target file format")
):
    """
    Validate if a conversion is supported.
    
    Args:
        source_format: The source file format
        target_format: The target file format
    
    Returns:
        Validation result
    """
    source = source_format.lower().lstrip('.')
    target = target_format.lower().lstrip('.')
    
    can_convert = ConverterFactory.can_convert(source, target)
    available_formats = ConverterFactory.get_available_output_formats(source)
    
    return {
        "source_format": source,
        "target_format": target,
        "supported": can_convert,
        "available_output_formats": available_formats
    }
