"""
Image Converter - Handles image format conversions
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import io

from app.services.base_converter import BaseConverter, ConversionResult
from app.config.settings import settings


class ImageConverter(BaseConverter):
    """Converter for image files using Pillow."""
    
    @property
    def supported_input_formats(self) -> List[str]:
        return ["jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "ico"]
    
    @property
    def supported_output_formats(self) -> List[str]:
        return ["jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "ico", "pdf"]
    
    @property
    def category(self) -> str:
        return "image"
    
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ConversionResult:
        """Convert image from one format to another."""
        options = options or {}
        quality = options.get("quality", settings.IMAGE_QUALITY)
        resize = options.get("resize")  # {"width": int, "height": int}
        
        try:
            # Run in thread pool to avoid blocking
            result = await asyncio.to_thread(
                self._convert_sync,
                input_path,
                output_path,
                target_format,
                quality,
                resize
            )
            return result
        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                output_format=target_format,
                error_message=str(e)
            )
    
    def _convert_sync(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        quality: int,
        resize: Optional[Dict[str, int]]
    ) -> ConversionResult:
        """Synchronous conversion logic."""
        target_format = target_format.lower().lstrip('.')
        
        # Open image
        with Image.open(input_path) as img:
            # Handle transparency for JPEG
            if target_format in ["jpg", "jpeg"] and img.mode in ["RGBA", "P"]:
                # Convert to RGB, using white background for transparency
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            
            # Resize if requested
            if resize:
                width = resize.get("width")
                height = resize.get("height")
                if width and height:
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                elif width:
                    ratio = width / img.width
                    img = img.resize((width, int(img.height * ratio)), Image.Resampling.LANCZOS)
                elif height:
                    ratio = height / img.height
                    img = img.resize((int(img.width * ratio), height), Image.Resampling.LANCZOS)
            
            # Save with appropriate options
            save_options = {}
            if target_format in ["jpg", "jpeg"]:
                save_options["quality"] = quality
                save_options["optimize"] = True
            elif target_format == "png":
                save_options["optimize"] = True
            elif target_format == "webp":
                save_options["quality"] = quality
            
            # Ensure output path has correct extension
            output_path = output_path.with_suffix(f".{target_format}")
            
            # Save the image
            if target_format == "pdf":
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                img.save(output_path, "PDF", resolution=settings.PDF_DPI)
            else:
                img.save(output_path, **save_options)
        
        # Get file size
        file_size = output_path.stat().st_size
        
        return ConversionResult(
            success=True,
            output_path=output_path,
            output_format=target_format,
            file_size=file_size,
            metadata={
                "quality": quality,
                "resized": resize is not None
            }
        )
