"""
File Handler Utilities
"""
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, BinaryIO
import aiofiles
import aiofiles.os

from app.config.settings import settings


class FileHandler:
    """Utility class for handling file operations."""
    
    @staticmethod
    async def save_upload(
        file_content: BinaryIO,
        filename: str,
        directory: Path = None
    ) -> Path:
        """
        Save an uploaded file asynchronously.
        
        Args:
            file_content: File content as binary IO
            filename: Name for the saved file
            directory: Directory to save to (default: upload_dir)
            
        Returns:
            Path to the saved file
        """
        directory = directory or settings.UPLOAD_DIR
        directory.mkdir(parents=True, exist_ok=True)
        
        file_path = directory / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = file_content.read()
            await f.write(content)
        
        return file_path
    
    @staticmethod
    async def delete_file(file_path: Path) -> bool:
        """
        Delete a file asynchronously.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            if file_path.exists():
                await aiofiles.os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    async def move_file(source: Path, destination: Path) -> Path:
        """
        Move a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Path to the moved file
        """
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return destination
    
    @staticmethod
    def get_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm (md5, sha1, sha256)
            
        Returns:
            Hexadecimal hash string
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size to human readable string.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Human readable size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    async def cleanup_old_files(
        directory: Path,
        max_age_hours: int = None
    ) -> int:
        """
        Clean up files older than max_age_hours.
        
        Args:
            directory: Directory to clean
            max_age_hours: Maximum age in hours (default from settings)
            
        Returns:
            Number of files deleted
        """
        max_age_hours = max_age_hours or settings.TEMP_FILE_EXPIRY_HOURS
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        if not directory.exists():
            return 0
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    try:
                        await aiofiles.os.remove(file_path)
                        deleted_count += 1
                    except Exception:
                        pass
        
        return deleted_count
    
    @staticmethod
    def list_files(
        directory: Path,
        pattern: str = "*"
    ) -> List[Path]:
        """
        List files in a directory matching a pattern.
        
        Args:
            directory: Directory to list
            pattern: Glob pattern to match
            
        Returns:
            List of file paths
        """
        if not directory.exists():
            return []
        return list(directory.glob(pattern))
