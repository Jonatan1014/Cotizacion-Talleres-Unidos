"""
Supported Formats Endpoints
"""
from typing import List
from fastapi import APIRouter

from app.models.schemas import SupportedFormats
from app.services.converter_factory import ConverterFactory

router = APIRouter()


@router.get(
    "",
    response_model=List[SupportedFormats],
    summary="Get Supported Formats",
    description="Get all supported conversion formats organized by category"
)
async def get_supported_formats() -> List[SupportedFormats]:
    """
    Get all supported file formats for conversion.
    
    Returns:
        List of supported formats by category (image, document, audio)
    """
    return ConverterFactory.get_all_supported_formats()


@router.get(
    "/{category}",
    response_model=SupportedFormats,
    summary="Get Formats by Category",
    description="Get supported formats for a specific category"
)
async def get_formats_by_category(category: str) -> SupportedFormats:
    """
    Get supported formats for a specific category.
    
    Args:
        category: The category (image, document, audio)
    
    Returns:
        Supported formats for the category
    """
    converter = ConverterFactory.get_converter(category)
    
    if not converter:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found. Available: image, document, audio"
        )
    
    return SupportedFormats(
        category=converter.category,
        input_formats=converter.supported_input_formats,
        output_formats=converter.supported_output_formats,
        description=f"Converter for {category} files"
    )


@router.get(
    "/output/{input_format}",
    summary="Get Available Output Formats",
    description="Get available output formats for a given input format"
)
async def get_output_formats(input_format: str):
    """
    Get available output formats for a given input format.
    
    Args:
        input_format: The input file format
    
    Returns:
        List of available output formats
    """
    input_fmt = input_format.lower().lstrip('.')
    output_formats = ConverterFactory.get_available_output_formats(input_fmt)
    
    return {
        "input_format": input_fmt,
        "output_formats": output_formats,
        "supported": len(output_formats) > 0
    }
