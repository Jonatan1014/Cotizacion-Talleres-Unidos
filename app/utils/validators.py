"""
File Validators
"""
import magic
from pathlib import Path
from typing import Tuple, Optional, List

from app.config.settings import settings


class FileValidator:
    """Utility class for validating files."""
    
    # MIME type mappings
    MIME_TYPES = {
        # Images
        "image/jpeg": ["jpg", "jpeg"],
        "image/png": ["png"],
        "image/gif": ["gif"],
        "image/bmp": ["bmp"],
        "image/webp": ["webp"],
        "image/tiff": ["tiff", "tif"],
        "image/x-icon": ["ico"],
        "image/svg+xml": ["svg"],
        
        # Documents
        "application/pdf": ["pdf"],
        "application/msword": ["doc"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ["docx"],
        "application/vnd.ms-excel": ["xls"],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ["xlsx"],
        "application/vnd.ms-powerpoint": ["ppt"],
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ["pptx"],
        "text/plain": ["txt"],
        "text/csv": ["csv"],
        "text/html": ["html", "htm"],
        "text/markdown": ["md"],
        
        # Audio
        "audio/mpeg": ["mp3"],
        "audio/wav": ["wav"],
        "audio/ogg": ["ogg"],
        "audio/flac": ["flac"],
        "audio/aac": ["aac"],
        "audio/mp4": ["m4a"],
        
        # Video
        "video/mp4": ["mp4"],
        "video/x-msvideo": ["avi"],
        "video/quicktime": ["mov"],
        "video/x-matroska": ["mkv"],
        "video/webm": ["webm"],
    }
    
    @classmethod
    def validate_extension(cls, filename: str) -> Tuple[bool, str]:
        """
        Validate file extension against allowed list.
        
        Args:
            filename: Name of the file
            
        Returns:
            Tuple of (is_valid, extension)
        """
        extension = Path(filename).suffix.lower()
        is_valid = extension in settings.ALLOWED_EXTENSIONS
        return is_valid, extension
    
    @classmethod
    def validate_size(cls, file_size: int) -> Tuple[bool, str]:
        """
        Validate file size against maximum allowed.
        
        Args:
            file_size: Size in bytes
            
        Returns:
            Tuple of (is_valid, message)
        """
        if file_size > settings.MAX_FILE_SIZE:
            return False, f"File size {file_size} exceeds maximum {settings.MAX_FILE_SIZE}"
        return True, "Size OK"
    
    @classmethod
    def validate_mime_type(cls, file_path: Path) -> Tuple[bool, str]:
        """
        Validate file MIME type using python-magic.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, detected_mime_type)
        """
        try:
            detected_mime = magic.from_file(str(file_path), mime=True)
            is_valid = detected_mime in cls.MIME_TYPES
            return is_valid, detected_mime
        except Exception as e:
            return False, f"Error detecting MIME type: {str(e)}"
    
    @classmethod
    def validate_file(
        cls,
        file_path: Path,
        expected_extension: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive file validation.
        
        Args:
            file_path: Path to the file
            expected_extension: Expected file extension (optional)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check file exists
        if not file_path.exists():
            return False, ["File does not exist"]
        
        # Check extension
        ext_valid, extension = cls.validate_extension(file_path.name)
        if not ext_valid:
            errors.append(f"Invalid extension: {extension}")
        
        # Check if expected extension matches
        if expected_extension:
            expected = expected_extension.lower().lstrip('.')
            actual = extension.lstrip('.')
            if expected != actual:
                errors.append(f"Extension mismatch: expected {expected}, got {actual}")
        
        # Check size
        file_size = file_path.stat().st_size
        size_valid, size_msg = cls.validate_size(file_size)
        if not size_valid:
            errors.append(size_msg)
        
        # Check MIME type
        mime_valid, mime_type = cls.validate_mime_type(file_path)
        if not mime_valid and "Error" not in mime_type:
            errors.append(f"Unsupported MIME type: {mime_type}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_extension_for_mime(cls, mime_type: str) -> Optional[str]:
        """
        Get file extension for a MIME type.
        
        Args:
            mime_type: MIME type string
            
        Returns:
            Primary extension for the MIME type
        """
        extensions = cls.MIME_TYPES.get(mime_type)
        return extensions[0] if extensions else None
    
    @classmethod
    def get_mime_for_extension(cls, extension: str) -> Optional[str]:
        """
        Get MIME type for a file extension.
        
        Args:
            extension: File extension
            
        Returns:
            MIME type for the extension
        """
        extension = extension.lower().lstrip('.')
        for mime_type, extensions in cls.MIME_TYPES.items():
            if extension in extensions:
                return mime_type
        return None
