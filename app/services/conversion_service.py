"""
Conversion Service - Main service for handling file conversions
"""
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, BinaryIO
import mimetypes

from app.config.settings import settings
from app.services.converter_factory import ConverterFactory
from app.services.base_converter import ConversionResult
from app.models.schemas import (
    ConversionResponse,
    ConversionStatus,
    FileInfo
)
from app.core.exceptions import (
    InvalidFileFormatError,
    ConversionError,
    FileTooLargeError,
    FileNotFoundError,
    UnsupportedConversionError
)


class ConversionService:
    """
    Main service for handling file conversion operations.
    
    This service orchestrates the conversion process:
    1. Validates input files
    2. Selects appropriate converter
    3. Performs conversion
    4. Returns results
    """
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.output_dir = settings.OUTPUT_DIR
        self.temp_dir = settings.TEMP_DIR
        
    async def convert_file(
        self,
        file_content: BinaryIO,
        filename: str,
        target_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ConversionResponse:
        """
        Convert a file to the target format.
        
        Args:
            file_content: File content as binary IO
            filename: Original filename
            target_format: Target format to convert to
            options: Additional conversion options
            
        Returns:
            ConversionResponse with conversion details
        """
        job_id = str(uuid.uuid4())
        
        # Validate file extension
        source_format = Path(filename).suffix.lower().lstrip('.')
        if not source_format:
            raise InvalidFileFormatError("unknown", settings.ALLOWED_EXTENSIONS)
        
        # Check if conversion is supported
        if not ConverterFactory.can_convert(source_format, target_format):
            raise UnsupportedConversionError(source_format, target_format)
        
        # Save uploaded file
        input_path = self.upload_dir / f"{job_id}_{filename}"
        try:
            content = file_content.read()
            
            # Check file size
            if len(content) > settings.MAX_FILE_SIZE:
                raise FileTooLargeError(len(content), settings.MAX_FILE_SIZE)
            
            with open(input_path, 'wb') as f:
                f.write(content)
        except FileTooLargeError:
            raise
        except Exception as e:
            raise ConversionError(f"Failed to save uploaded file: {str(e)}")
        
        # Get file info
        original_file = self._get_file_info(input_path, filename)
        
        # Get converter and perform conversion
        converter = ConverterFactory.get_converter_for_format(source_format)
        if not converter:
            self._cleanup_file(input_path)
            raise InvalidFileFormatError(source_format)
        
        # Set output path
        output_filename = f"{job_id}_converted.{target_format.lstrip('.')}"
        output_path = self.output_dir / output_filename
        
        # Perform conversion
        result = await converter.convert(
            input_path=input_path,
            output_path=output_path,
            target_format=target_format,
            options=options
        )
        
        if not result.success:
            self._cleanup_file(input_path)
            raise ConversionError(result.error_message or "Conversion failed")
        
        # Build response
        converted_file = self._get_file_info(result.output_path, output_filename) if result.output_path else None
        
        return ConversionResponse(
            job_id=job_id,
            status=ConversionStatus.COMPLETED,
            original_file=original_file,
            converted_file=converted_file,
            target_format=target_format,
            download_url=f"/api/v1/conversion/download/{job_id}",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
    
    def get_converted_file_path(self, job_id: str) -> Path:
        """
        Get the path to a converted file.
        
        Args:
            job_id: The conversion job ID
            
        Returns:
            Path to the converted file
        """
        # Find file with job_id prefix
        for file in self.output_dir.iterdir():
            if file.name.startswith(f"{job_id}_"):
                return file
        
        raise FileNotFoundError(job_id)
    
    def cleanup_job_files(self, job_id: str) -> bool:
        """
        Clean up files associated with a conversion job.
        
        Args:
            job_id: The conversion job ID
            
        Returns:
            True if cleanup was successful
        """
        cleaned = False
        
        # Clean upload directory
        for file in self.upload_dir.iterdir():
            if file.name.startswith(f"{job_id}_"):
                self._cleanup_file(file)
                cleaned = True
        
        # Clean output directory
        for file in self.output_dir.iterdir():
            if file.name.startswith(f"{job_id}_"):
                self._cleanup_file(file)
                cleaned = True
        
        return cleaned
    
    def _get_file_info(self, file_path: Path, original_filename: str) -> FileInfo:
        """Get file information."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return FileInfo(
            filename=file_path.name,
            original_filename=original_filename,
            size=file_path.stat().st_size,
            mime_type=mime_type or "application/octet-stream",
            extension=file_path.suffix.lower()
        )
    
    def _cleanup_file(self, file_path: Path) -> None:
        """Safely delete a file."""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # Log error in production


# Singleton instance
conversion_service = ConversionService()
