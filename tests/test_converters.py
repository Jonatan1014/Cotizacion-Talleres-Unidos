"""
Tests for converter services
"""
import pytest
from pathlib import Path

from app.services.converter_factory import ConverterFactory
from app.services.converters.image_converter import ImageConverter


class TestConverterFactory:
    """Tests for ConverterFactory."""
    
    def test_get_converter_for_image(self):
        """Test getting converter for image format."""
        converter = ConverterFactory.get_converter_for_format("jpg")
        assert converter is not None
        assert converter.category == "image"
    
    def test_get_converter_for_audio(self):
        """Test getting converter for audio format."""
        converter = ConverterFactory.get_converter_for_format("mp3")
        assert converter is not None
        assert converter.category == "audio"
    
    def test_get_converter_for_document(self):
        """Test getting converter for document format."""
        converter = ConverterFactory.get_converter_for_format("pdf")
        assert converter is not None
        assert converter.category == "document"
    
    def test_can_convert_valid(self):
        """Test can_convert for valid conversion."""
        assert ConverterFactory.can_convert("jpg", "png") is True
        assert ConverterFactory.can_convert("png", "webp") is True
    
    def test_can_convert_invalid(self):
        """Test can_convert for invalid conversion."""
        assert ConverterFactory.can_convert("jpg", "mp3") is False
        assert ConverterFactory.can_convert("unknown", "png") is False
    
    def test_get_all_supported_formats(self):
        """Test getting all supported formats."""
        formats = ConverterFactory.get_all_supported_formats()
        assert len(formats) > 0
        
        categories = [f.category for f in formats]
        assert "image" in categories
        assert "document" in categories
        assert "audio" in categories


class TestImageConverter:
    """Tests for ImageConverter."""
    
    def test_supported_formats(self):
        """Test supported formats."""
        converter = ImageConverter()
        
        assert "jpg" in converter.supported_input_formats
        assert "png" in converter.supported_input_formats
        assert "png" in converter.supported_output_formats
        assert "webp" in converter.supported_output_formats
    
    def test_can_convert(self):
        """Test can_convert method."""
        converter = ImageConverter()
        
        assert converter.can_convert("jpg", "png") is True
        assert converter.can_convert("png", "webp") is True
        assert converter.can_convert("gif", "pdf") is True
        assert converter.can_convert("mp3", "png") is False
    
    @pytest.mark.asyncio
    async def test_convert_image(self, sample_image, tmp_path):
        """Test image conversion."""
        converter = ImageConverter()
        output_path = tmp_path / "output.png"
        
        result = await converter.convert(
            input_path=sample_image,
            output_path=output_path,
            target_format="png"
        )
        
        assert result.success is True
        assert result.output_path.exists()
        assert result.output_format == "png"
