"""
Converter Factory - Creates appropriate converter based on file type
"""
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.services.base_converter import BaseConverter
from app.services.converters.image_converter import ImageConverter
from app.services.converters.document_converter import DocumentConverter
from app.services.converters.audio_converter import AudioConverter
from app.models.schemas import SupportedFormats, ConversionCategory


class ConverterFactory:
    """
    Factory class for creating file converters.
    
    Uses the factory pattern to return the appropriate converter
    based on file type or format.
    """
    
    _converters: Dict[str, BaseConverter] = {}
    
    @classmethod
    def _initialize_converters(cls) -> None:
        """Initialize all available converters."""
        if not cls._converters:
            cls._converters = {
                "image": ImageConverter(),
                "document": DocumentConverter(),
                "audio": AudioConverter(),
            }
    
    @classmethod
    def get_converter(cls, category: str) -> Optional[BaseConverter]:
        """Get converter by category."""
        cls._initialize_converters()
        return cls._converters.get(category.lower())
    
    @classmethod
    def get_converter_for_format(cls, format: str) -> Optional[BaseConverter]:
        """
        Get appropriate converter for a given file format.
        
        Args:
            format: File extension (with or without dot)
            
        Returns:
            Appropriate converter or None if not supported
        """
        cls._initialize_converters()
        format = format.lower().lstrip('.')
        
        for converter in cls._converters.values():
            if format in converter.supported_input_formats:
                return converter
        
        return None
    
    @classmethod
    def get_converter_for_file(cls, file_path: Path) -> Optional[BaseConverter]:
        """
        Get appropriate converter for a given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Appropriate converter or None if not supported
        """
        extension = file_path.suffix.lower().lstrip('.')
        return cls.get_converter_for_format(extension)
    
    @classmethod
    def can_convert(cls, source_format: str, target_format: str) -> bool:
        """
        Check if conversion between formats is possible.
        
        Args:
            source_format: Source file format
            target_format: Target file format
            
        Returns:
            True if conversion is supported, False otherwise
        """
        converter = cls.get_converter_for_format(source_format)
        if converter:
            return converter.can_convert(source_format, target_format)
        return False
    
    @classmethod
    def get_all_supported_formats(cls) -> List[SupportedFormats]:
        """Get all supported formats across all converters."""
        cls._initialize_converters()
        
        formats = []
        for category, converter in cls._converters.items():
            formats.append(SupportedFormats(
                category=ConversionCategory(category),
                input_formats=converter.supported_input_formats,
                output_formats=converter.supported_output_formats,
                description=f"Converter for {category} files"
            ))
        
        return formats
    
    @classmethod
    def get_available_output_formats(cls, input_format: str) -> List[str]:
        """
        Get available output formats for a given input format.
        
        Args:
            input_format: The input file format
            
        Returns:
            List of available output formats
        """
        converter = cls.get_converter_for_format(input_format)
        if converter:
            return converter.supported_output_formats
        return []
    
    @classmethod
    def register_converter(cls, category: str, converter: BaseConverter) -> None:
        """
        Register a custom converter.
        
        Args:
            category: Category name for the converter
            converter: Converter instance
        """
        cls._initialize_converters()
        cls._converters[category.lower()] = converter
