"""
Base Converter - Abstract base class for all converters
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    success: bool
    output_path: Optional[Path]
    output_format: str
    file_size: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseConverter(ABC):
    """
    Abstract base class for file converters.
    
    All specific converters (image, document, audio, etc.) should inherit from this class.
    """
    
    @property
    @abstractmethod
    def supported_input_formats(self) -> List[str]:
        """Return list of supported input formats."""
        pass
    
    @property
    @abstractmethod
    def supported_output_formats(self) -> List[str]:
        """Return list of supported output formats."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Return the category of the converter (image, document, audio, etc.)."""
        pass
    
    def can_convert(self, input_format: str, output_format: str) -> bool:
        """Check if conversion between formats is supported."""
        input_format = input_format.lower().lstrip('.')
        output_format = output_format.lower().lstrip('.')
        return (
            input_format in self.supported_input_formats and
            output_format in self.supported_output_formats
        )
    
    @abstractmethod
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ConversionResult:
        """
        Convert a file from one format to another.
        
        Args:
            input_path: Path to the input file
            output_path: Path where the output file should be saved
            target_format: Target format to convert to
            options: Additional conversion options
            
        Returns:
            ConversionResult with details of the conversion
        """
        pass
    
    def validate_input(self, input_path: Path) -> bool:
        """Validate that the input file exists and is readable."""
        return input_path.exists() and input_path.is_file()
    
    def get_format_info(self, format: str) -> Dict[str, Any]:
        """Get information about a specific format."""
        return {
            "format": format,
            "is_input_supported": format in self.supported_input_formats,
            "is_output_supported": format in self.supported_output_formats,
            "category": self.category
        }
