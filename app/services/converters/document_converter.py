"""
Document Converter - Handles document format conversions
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import shutil

from app.services.base_converter import BaseConverter, ConversionResult


class DocumentConverter(BaseConverter):
    """
    Converter for document files.
    
    Uses LibreOffice for document conversions when available,
    with fallback options for specific conversions.
    """
    
    @property
    def supported_input_formats(self) -> List[str]:
        return ["pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "csv", "html", "odt", "ods", "odp", "rtf"]
    
    @property
    def supported_output_formats(self) -> List[str]:
        return ["pdf", "docx", "txt", "html", "odt", "rtf"]
    
    @property
    def category(self) -> str:
        return "document"
    
    def _get_libreoffice_path(self) -> Optional[str]:
        """Find LibreOffice executable path."""
        # Check common paths
        paths = [
            "libreoffice",
            "soffice",
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
        ]
        
        for path in paths:
            if shutil.which(path):
                return path
        
        return None
    
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ConversionResult:
        """Convert document from one format to another."""
        options = options or {}
        target_format = target_format.lower().lstrip('.')
        
        try:
            # Special case: txt to txt (no conversion needed)
            if input_path.suffix.lower().lstrip('.') == target_format:
                shutil.copy(input_path, output_path)
                return ConversionResult(
                    success=True,
                    output_path=output_path,
                    output_format=target_format,
                    file_size=output_path.stat().st_size
                )
            
            # Try LibreOffice conversion
            libreoffice_path = self._get_libreoffice_path()
            if libreoffice_path:
                result = await self._convert_with_libreoffice(
                    input_path,
                    output_path,
                    target_format,
                    libreoffice_path
                )
                return result
            
            # Fallback for specific conversions
            result = await self._convert_fallback(
                input_path,
                output_path,
                target_format,
                options
            )
            return result
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                output_format=target_format,
                error_message=str(e)
            )
    
    async def _convert_with_libreoffice(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        libreoffice_path: str
    ) -> ConversionResult:
        """Convert using LibreOffice."""
        output_dir = output_path.parent
        
        # Build LibreOffice command
        cmd = [
            libreoffice_path,
            "--headless",
            "--convert-to", target_format,
            "--outdir", str(output_dir),
            str(input_path)
        ]
        
        # Run conversion
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return ConversionResult(
                success=False,
                output_path=None,
                output_format=target_format,
                error_message=f"LibreOffice conversion failed: {stderr.decode()}"
            )
        
        # Find output file (LibreOffice names it based on input)
        expected_output = output_dir / f"{input_path.stem}.{target_format}"
        
        if expected_output.exists():
            # Rename to desired output path if different
            if expected_output != output_path:
                final_path = output_path.with_suffix(f".{target_format}")
                shutil.move(expected_output, final_path)
            else:
                final_path = expected_output
            
            return ConversionResult(
                success=True,
                output_path=final_path,
                output_format=target_format,
                file_size=final_path.stat().st_size
            )
        
        return ConversionResult(
            success=False,
            output_path=None,
            output_format=target_format,
            error_message="Output file not found after conversion"
        )
    
    async def _convert_fallback(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        options: Dict[str, Any]
    ) -> ConversionResult:
        """Fallback conversion methods for when LibreOffice is not available."""
        input_format = input_path.suffix.lower().lstrip('.')
        
        # txt conversions
        if input_format == "txt" and target_format == "html":
            return await self._txt_to_html(input_path, output_path)
        
        if target_format == "txt":
            return await self._to_txt(input_path, output_path)
        
        return ConversionResult(
            success=False,
            output_path=None,
            output_format=target_format,
            error_message=f"Conversion from {input_format} to {target_format} requires LibreOffice"
        )
    
    async def _txt_to_html(self, input_path: Path, output_path: Path) -> ConversionResult:
        """Convert plain text to HTML."""
        content = input_path.read_text(encoding='utf-8')
        
        # Simple HTML conversion
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{input_path.stem}</title>
</head>
<body>
<pre>{content}</pre>
</body>
</html>"""
        
        output_path = output_path.with_suffix('.html')
        output_path.write_text(html_content, encoding='utf-8')
        
        return ConversionResult(
            success=True,
            output_path=output_path,
            output_format="html",
            file_size=output_path.stat().st_size
        )
    
    async def _to_txt(self, input_path: Path, output_path: Path) -> ConversionResult:
        """Extract text content to txt file."""
        input_format = input_path.suffix.lower().lstrip('.')
        
        try:
            if input_format in ["txt", "csv"]:
                content = input_path.read_text(encoding='utf-8')
            else:
                return ConversionResult(
                    success=False,
                    output_path=None,
                    output_format="txt",
                    error_message=f"Cannot extract text from {input_format} without additional libraries"
                )
            
            output_path = output_path.with_suffix('.txt')
            output_path.write_text(content, encoding='utf-8')
            
            return ConversionResult(
                success=True,
                output_path=output_path,
                output_format="txt",
                file_size=output_path.stat().st_size
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                output_format="txt",
                error_message=str(e)
            )
