"""
Smart Converter Service - Auto-detección y conversión inteligente de archivos
"""
import asyncio
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import BinaryIO, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import mimetypes

from app.config.settings import settings


class DetectedFileType(str, Enum):
    """Tipos de archivo detectados."""
    WORD = "word"
    EXCEL = "excel"
    PDF = "pdf"
    UNKNOWN = "unknown"


class OutputFormat(str, Enum):
    """Formatos de salida."""
    PDF = "pdf"
    JPG = "jpg"


@dataclass
class ConversionRule:
    """Regla de conversión."""
    source_type: DetectedFileType
    target_format: OutputFormat
    condition: Optional[str] = None  # e.g., "single_page" for PDFs


@dataclass
class SmartConversionResult:
    """Resultado de conversión inteligente."""
    success: bool
    output_data: Optional[bytes]
    output_format: str
    output_filename: str
    original_type: DetectedFileType
    mime_type: str
    file_size: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FileTypeDetector:
    """Detector de tipos de archivo."""
    
    # Mapeo de extensiones a tipos
    EXTENSION_MAP = {
        # Word
        ".doc": DetectedFileType.WORD,
        ".docx": DetectedFileType.WORD,
        ".odt": DetectedFileType.WORD,
        ".rtf": DetectedFileType.WORD,
        # Excel
        ".xls": DetectedFileType.EXCEL,
        ".xlsx": DetectedFileType.EXCEL,
        ".ods": DetectedFileType.EXCEL,
        ".csv": DetectedFileType.EXCEL,
        # PDF
        ".pdf": DetectedFileType.PDF,
    }
    
    # Mapeo de MIME types
    MIME_MAP = {
        # Word
        "application/msword": DetectedFileType.WORD,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DetectedFileType.WORD,
        "application/vnd.oasis.opendocument.text": DetectedFileType.WORD,
        "application/rtf": DetectedFileType.WORD,
        # Excel
        "application/vnd.ms-excel": DetectedFileType.EXCEL,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DetectedFileType.EXCEL,
        "application/vnd.oasis.opendocument.spreadsheet": DetectedFileType.EXCEL,
        "text/csv": DetectedFileType.EXCEL,
        # PDF
        "application/pdf": DetectedFileType.PDF,
    }
    
    @classmethod
    def detect_from_filename(cls, filename: str) -> DetectedFileType:
        """Detectar tipo de archivo por extensión."""
        ext = Path(filename).suffix.lower()
        return cls.EXTENSION_MAP.get(ext, DetectedFileType.UNKNOWN)
    
    @classmethod
    def detect_from_mime(cls, mime_type: str) -> DetectedFileType:
        """Detectar tipo de archivo por MIME type."""
        return cls.MIME_MAP.get(mime_type, DetectedFileType.UNKNOWN)
    
    @classmethod
    def detect(cls, filename: str, content_type: Optional[str] = None) -> DetectedFileType:
        """
        Detectar tipo de archivo usando múltiples métodos.
        Prioriza MIME type si está disponible, luego extensión.
        """
        if content_type:
            detected = cls.detect_from_mime(content_type)
            if detected != DetectedFileType.UNKNOWN:
                return detected
        
        return cls.detect_from_filename(filename)


class SmartConverter:
    """
    Servicio de conversión inteligente.
    
    Detecta automáticamente el tipo de archivo y aplica las reglas de conversión:
    - Word → PDF
    - Excel → PDF
    - PDF (1 página) → JPG
    """
    
    # Reglas de conversión por defecto
    CONVERSION_RULES = {
        DetectedFileType.WORD: OutputFormat.PDF,
        DetectedFileType.EXCEL: OutputFormat.PDF,
        DetectedFileType.PDF: OutputFormat.JPG,  # Solo si tiene 1 página
    }
    
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Asegurar que existen los directorios necesarios."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_libreoffice_path(self) -> Optional[str]:
        """Encontrar ejecutable de LibreOffice."""
        paths = [
            "libreoffice",
            "soffice",
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
        for path in paths:
            if shutil.which(path):
                return path
        return None
    
    async def convert(
        self,
        file_content: BinaryIO,
        filename: str,
        content_type: Optional[str] = None
    ) -> SmartConversionResult:
        """
        Procesar y convertir archivo automáticamente.
        
        Args:
            file_content: Contenido del archivo
            filename: Nombre original del archivo
            content_type: MIME type del archivo (opcional)
            
        Returns:
            SmartConversionResult con el archivo convertido
        """
        # Detectar tipo de archivo
        file_type = FileTypeDetector.detect(filename, content_type)
        
        if file_type == DetectedFileType.UNKNOWN:
            return SmartConversionResult(
                success=False,
                output_data=None,
                output_format="",
                output_filename="",
                original_type=file_type,
                mime_type="",
                file_size=0,
                error_message=f"Tipo de archivo no soportado: {filename}"
            )
        
        # Leer contenido
        content = file_content.read()
        
        # Verificar tamaño
        if len(content) > settings.MAX_FILE_SIZE:
            return SmartConversionResult(
                success=False,
                output_data=None,
                output_format="",
                output_filename="",
                original_type=file_type,
                mime_type="",
                file_size=len(content),
                error_message=f"Archivo demasiado grande: {len(content)} bytes (máx: {settings.MAX_FILE_SIZE})"
            )
        
        # Procesar según tipo
        try:
            if file_type == DetectedFileType.WORD:
                return await self._convert_word_to_pdf(content, filename)
            elif file_type == DetectedFileType.EXCEL:
                return await self._convert_excel_to_pdf(content, filename)
            elif file_type == DetectedFileType.PDF:
                return await self._convert_pdf_to_image(content, filename)
            else:
                return SmartConversionResult(
                    success=False,
                    output_data=None,
                    output_format="",
                    output_filename="",
                    original_type=file_type,
                    mime_type="",
                    file_size=0,
                    error_message="Tipo de archivo no procesable"
                )
        except Exception as e:
            return SmartConversionResult(
                success=False,
                output_data=None,
                output_format="",
                output_filename="",
                original_type=file_type,
                mime_type="",
                file_size=0,
                error_message=f"Error en conversión: {str(e)}"
            )
    
    async def _convert_word_to_pdf(
        self,
        content: bytes,
        filename: str
    ) -> SmartConversionResult:
        """Convertir documento Word a PDF."""
        return await self._convert_office_to_pdf(
            content, filename, DetectedFileType.WORD
        )
    
    async def _convert_excel_to_pdf(
        self,
        content: bytes,
        filename: str
    ) -> SmartConversionResult:
        """Convertir documento Excel a PDF."""
        return await self._convert_office_to_pdf(
            content, filename, DetectedFileType.EXCEL
        )
    
    async def _convert_office_to_pdf(
        self,
        content: bytes,
        filename: str,
        file_type: DetectedFileType
    ) -> SmartConversionResult:
        """Convertir documento Office a PDF usando LibreOffice."""
        libreoffice = self._get_libreoffice_path()
        
        if not libreoffice:
            return SmartConversionResult(
                success=False,
                output_data=None,
                output_format="pdf",
                output_filename="",
                original_type=file_type,
                mime_type="",
                file_size=0,
                error_message="LibreOffice no está instalado"
            )
        
        # Crear archivos temporales
        with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / filename
            
            # Escribir archivo de entrada
            input_file.write_bytes(content)
            
            # Comando de conversión
            cmd = [
                libreoffice,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(temp_path),
                str(input_file)
            ]
            
            # Ejecutar conversión
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                return SmartConversionResult(
                    success=False,
                    output_data=None,
                    output_format="pdf",
                    output_filename="",
                    original_type=file_type,
                    mime_type="",
                    file_size=0,
                    error_message=f"Error en LibreOffice: {stderr.decode()}"
                )
            
            # Buscar archivo PDF generado
            pdf_file = temp_path / f"{Path(filename).stem}.pdf"
            
            if not pdf_file.exists():
                return SmartConversionResult(
                    success=False,
                    output_data=None,
                    output_format="pdf",
                    output_filename="",
                    original_type=file_type,
                    mime_type="",
                    file_size=0,
                    error_message="No se generó el archivo PDF"
                )
            
            # Leer resultado
            output_data = pdf_file.read_bytes()
            output_filename = f"{Path(filename).stem}.pdf"
            
            return SmartConversionResult(
                success=True,
                output_data=output_data,
                output_format="pdf",
                output_filename=output_filename,
                original_type=file_type,
                mime_type="application/pdf",
                file_size=len(output_data),
                metadata={"source_format": Path(filename).suffix.lower()}
            )
    
    async def _convert_pdf_to_image(
        self,
        content: bytes,
        filename: str
    ) -> SmartConversionResult:
        """
        Convertir PDF a imagen JPG.
        Solo convierte si el PDF tiene exactamente 1 página.
        """
        try:
            # Intentar usar pdf2image (basado en poppler)
            from pdf2image import convert_from_bytes
            from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError
            
            # Obtener información del PDF
            try:
                images = convert_from_bytes(
                    content,
                    dpi=settings.PDF_DPI,
                    first_page=1,
                    last_page=1,
                    fmt='jpeg'
                )
            except PDFInfoNotInstalledError:
                return SmartConversionResult(
                    success=False,
                    output_data=None,
                    output_format="jpg",
                    output_filename="",
                    original_type=DetectedFileType.PDF,
                    mime_type="",
                    file_size=0,
                    error_message="Poppler no está instalado (requerido para convertir PDF a imagen)"
                )
            
            # Verificar número de páginas
            page_count = self._get_pdf_page_count(content)
            
            if page_count != 1:
                return SmartConversionResult(
                    success=False,
                    output_data=None,
                    output_format="jpg",
                    output_filename="",
                    original_type=DetectedFileType.PDF,
                    mime_type="",
                    file_size=0,
                    error_message=f"El PDF tiene {page_count} páginas. Solo se convierten PDFs de 1 página.",
                    metadata={"page_count": page_count}
                )
            
            if not images:
                return SmartConversionResult(
                    success=False,
                    output_data=None,
                    output_format="jpg",
                    output_filename="",
                    original_type=DetectedFileType.PDF,
                    mime_type="",
                    file_size=0,
                    error_message="No se pudo convertir el PDF a imagen"
                )
            
            # Convertir imagen a bytes
            import io
            output_buffer = io.BytesIO()
            images[0].save(output_buffer, format='JPEG', quality=settings.IMAGE_QUALITY)
            output_data = output_buffer.getvalue()
            output_filename = f"{Path(filename).stem}.jpg"
            
            return SmartConversionResult(
                success=True,
                output_data=output_data,
                output_format="jpg",
                output_filename=output_filename,
                original_type=DetectedFileType.PDF,
                mime_type="image/jpeg",
                file_size=len(output_data),
                metadata={"page_count": 1, "dpi": settings.PDF_DPI}
            )
            
        except ImportError:
            # Fallback: usar ghostscript directamente
            return await self._convert_pdf_to_image_gs(content, filename)
    
    async def _convert_pdf_to_image_gs(
        self,
        content: bytes,
        filename: str
    ) -> SmartConversionResult:
        """Convertir PDF a imagen usando Ghostscript directamente."""
        gs_path = shutil.which("gs") or shutil.which("gswin64c")
        
        if not gs_path:
            return SmartConversionResult(
                success=False,
                output_data=None,
                output_format="jpg",
                output_filename="",
                original_type=DetectedFileType.PDF,
                mime_type="",
                file_size=0,
                error_message="Ghostscript no está instalado"
            )
        
        # Verificar páginas primero
        page_count = self._get_pdf_page_count(content)
        
        if page_count != 1:
            return SmartConversionResult(
                success=False,
                output_data=None,
                output_format="jpg",
                output_filename="",
                original_type=DetectedFileType.PDF,
                mime_type="",
                file_size=0,
                error_message=f"El PDF tiene {page_count} páginas. Solo se convierten PDFs de 1 página.",
                metadata={"page_count": page_count}
            )
        
        with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / filename
            output_file = temp_path / f"{Path(filename).stem}.jpg"
            
            input_file.write_bytes(content)
            
            # Comando Ghostscript
            cmd = [
                gs_path,
                "-dNOPAUSE",
                "-dBATCH",
                "-dSAFER",
                "-sDEVICE=jpeg",
                f"-r{settings.PDF_DPI}",
                "-dJPEGQ=85",
                f"-sOutputFile={output_file}",
                str(input_file)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if not output_file.exists():
                return SmartConversionResult(
                    success=False,
                    output_data=None,
                    output_format="jpg",
                    output_filename="",
                    original_type=DetectedFileType.PDF,
                    mime_type="",
                    file_size=0,
                    error_message=f"Error en Ghostscript: {stderr.decode()}"
                )
            
            output_data = output_file.read_bytes()
            output_filename = f"{Path(filename).stem}.jpg"
            
            return SmartConversionResult(
                success=True,
                output_data=output_data,
                output_format="jpg",
                output_filename=output_filename,
                original_type=DetectedFileType.PDF,
                mime_type="image/jpeg",
                file_size=len(output_data),
                metadata={"page_count": 1, "dpi": settings.PDF_DPI}
            )
    
    def _get_pdf_page_count(self, content: bytes) -> int:
        """Obtener número de páginas de un PDF."""
        try:
            # Intento 1: usar PyPDF2/pypdf
            try:
                from pypdf import PdfReader
                import io
                reader = PdfReader(io.BytesIO(content))
                return len(reader.pages)
            except ImportError:
                pass
            
            # Intento 2: usar pdfinfo (poppler)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                result = subprocess.run(
                    ['pdfinfo', tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                for line in result.stdout.split('\n'):
                    if line.startswith('Pages:'):
                        return int(line.split(':')[1].strip())
            finally:
                Path(tmp_path).unlink(missing_ok=True)
            
            # Fallback: buscar en el contenido del PDF
            content_str = content.decode('latin-1', errors='ignore')
            import re
            match = re.search(r'/Count\s+(\d+)', content_str)
            if match:
                return int(match.group(1))
            
            return 0
            
        except Exception:
            return 0


# Instancia singleton
smart_converter = SmartConverter()
