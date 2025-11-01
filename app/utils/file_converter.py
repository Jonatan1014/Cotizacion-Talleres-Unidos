"""
Utilidad de Conversión de Archivos

Maneja la conversión de documentos office usando herramientas del sistema:
- PDF a PNG (solo PDFs de una página)
- DOCX a PDF (usando LibreOffice)
- XLSX/XLSM a PDF (usando LibreOffice)

NOTA: Requiere herramientas instaladas: poppler-utils, libreoffice, xvfb
      En Windows, estas herramientas deben estar en el PATH o ejecutarse en Docker.
"""

import subprocess
import os
import shutil
import uuid
import re
from pathlib import Path
from typing import Optional
from app.config import settings


class FileConverter:
    """Clase de utilidad para convertir formatos de documentos"""
    
    def __init__(self):
        self.processed_dir = settings.processed_dir
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def convert_pdf_to_png(self, pdf_path: str) -> str:
        """
        Convierte PDF a PNG si es de una sola página, de lo contrario copia el original.
        
        Args:
            pdf_path: Ruta absoluta al archivo PDF
            
        Returns:
            Ruta absoluta al archivo procesado (PNG o PDF)
            
        Raises:
            Exception: Si la conversión falla
        """
        if not os.path.exists(pdf_path) or not os.path.isfile(pdf_path):
            raise Exception(f'El archivo PDF no existe o no es legible: {pdf_path}')
        
        # Obtener número de páginas usando pdfinfo
        try:
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            pages = 0
            for line in result.stdout.split('\n'):
                match = re.match(r'^Pages:\s+(\d+)', line)
                if match:
                    pages = int(match.group(1))
                    break
            
            # Si el PDF tiene más de 1 página, copiar el archivo original sin cambios
            if pages > 1:
                original_name = Path(pdf_path).stem
                unique_id = uuid.uuid4().hex[:12]
                new_filename = f"{unique_id}-{original_name}.pdf"
                output_path = os.path.join(self.processed_dir, new_filename)
                
                shutil.copy(pdf_path, output_path)
                return output_path
            
            # Si el PDF tiene solo 1 página, convertir a PNG
            original_name = Path(pdf_path).stem
            unique_id = uuid.uuid4().hex[:12]
            new_filename = f"{unique_id}-{original_name}"
            output_base = os.path.join(self.processed_dir, new_filename)
            
            # Convertir usando pdftoppm
            subprocess.run(
                ['pdftoppm', '-png', '-f', '1', '-l', '1', pdf_path, output_base],
                check=True,
                capture_output=True
            )
            
            # pdftoppm crea archivos con sufijo -1
            created_file = f"{output_base}-1.png"
            final_path = f"{output_base}.png"
            
            if os.path.exists(created_file):
                os.rename(created_file, final_path)
            
            if not os.path.exists(final_path):
                raise Exception('El archivo PNG no fue creado')
            
            return final_path
            
        except FileNotFoundError:
            # Si pdfinfo/pdftoppm no están disponibles (Windows), solo copiar el PDF
            original_name = Path(pdf_path).stem
            unique_id = uuid.uuid4().hex[:12]
            new_filename = f"{unique_id}-{original_name}.pdf"
            output_path = os.path.join(self.processed_dir, new_filename)
            shutil.copy(pdf_path, output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f'La conversión de PDF falló: {e.stderr}')
    
    def convert_docx_to_pdf(self, docx_path: str) -> str:
        """
        Convierte DOCX a PDF usando LibreOffice.
        
        Args:
            docx_path: Ruta absoluta al archivo DOCX
            
        Returns:
            Ruta absoluta al archivo PDF convertido
            
        Raises:
            Exception: Si la conversión falla
        """
        if not os.path.exists(docx_path) or not os.path.isfile(docx_path):
            raise Exception(f'El archivo DOCX no existe o no es legible: {docx_path}')
        
        # Crear directorio temporal para conversión
        temp_dir = f'/tmp/libreoffice_{uuid.uuid4().hex}'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Copiar archivo a directorio temporal
            temp_file = os.path.join(temp_dir, os.path.basename(docx_path))
            shutil.copy(docx_path, temp_file)
            os.chmod(temp_file, 0o644)
            
            # Convertir usando LibreOffice
            env = os.environ.copy()
            env['HOME'] = '/tmp'
            
            result = subprocess.run([
                'timeout', '60',
                'xvfb-run', '--auto-servernum', '--server-args=-screen 0 1024x768x24',
                'libreoffice', '--headless', '--invisible', '--nodefault',
                '--nofirststartwizard', '--nolockcheck', '--nologo', '--norestore',
                '--convert-to', 'pdf', '--outdir', temp_dir, temp_file
            ], 
                capture_output=True,
                text=True,
                env=env,
                timeout=settings.conversion_timeout
            )
            
            # Generar nombre de archivo de salida
            original_name = Path(docx_path).stem
            unique_id = uuid.uuid4().hex[:12]
            new_filename = f"{unique_id}-{original_name}.pdf"
            final_path = os.path.join(self.processed_dir, new_filename)
            
            # Buscar archivo convertido
            converted_name = Path(docx_path).stem + '.pdf'
            converted_file = os.path.join(temp_dir, converted_name)
            
            if os.path.exists(converted_file):
                shutil.move(converted_file, final_path)
            else:
                raise Exception(f'LibreOffice no pudo crear el PDF. Salida: {result.stdout} {result.stderr}')
            
            if not os.path.exists(final_path):
                raise Exception('El archivo PDF no fue creado')
            
            return final_path
            
        except FileNotFoundError:
            # Si LibreOffice no está disponible, solo copiar el archivo original
            original_name = Path(docx_path).stem
            unique_id = uuid.uuid4().hex[:12]
            new_filename = f"{unique_id}-{original_name}.docx"
            output_path = os.path.join(self.processed_dir, new_filename)
            shutil.copy(docx_path, output_path)
            return output_path
        finally:
            # Limpiar directorio temporal
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def convert_excel_to_pdf(self, excel_path: str) -> str:
        """
        Convierte XLSX/XLSM a PDF usando LibreOffice.
        
        Args:
            excel_path: Ruta absoluta al archivo Excel
            
        Returns:
            Ruta absoluta al archivo PDF convertido
            
        Raises:
            Exception: Si la conversión falla
        """
        if not os.path.exists(excel_path) or not os.path.isfile(excel_path):
            raise Exception(f'El archivo Excel no existe o no es legible: {excel_path}')
        
        # Crear directorio temporal para conversión
        temp_dir = f'/tmp/libreoffice_{uuid.uuid4().hex}'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Copiar archivo a directorio temporal
            temp_file = os.path.join(temp_dir, os.path.basename(excel_path))
            shutil.copy(excel_path, temp_file)
            os.chmod(temp_file, 0o644)
            
            # Convertir usando LibreOffice
            env = os.environ.copy()
            env['HOME'] = '/tmp'
            
            result = subprocess.run([
                'timeout', '60',
                'xvfb-run', '--auto-servernum', '--server-args=-screen 0 1024x768x24',
                'libreoffice', '--headless', '--invisible', '--nodefault',
                '--nofirststartwizard', '--nolockcheck', '--nologo', '--norestore',
                '--convert-to', 'pdf', '--outdir', temp_dir, temp_file
            ],
                capture_output=True,
                text=True,
                env=env,
                timeout=settings.conversion_timeout
            )
            
            # Generar nombre de archivo de salida
            original_name = Path(excel_path).stem
            unique_id = uuid.uuid4().hex[:12]
            new_filename = f"{unique_id}-{original_name}.pdf"
            final_path = os.path.join(self.processed_dir, new_filename)
            
            # Buscar archivo convertido
            converted_name = Path(excel_path).stem + '.pdf'
            converted_file = os.path.join(temp_dir, converted_name)
            
            if os.path.exists(converted_file):
                shutil.move(converted_file, final_path)
            else:
                raise Exception(f'LibreOffice no pudo crear el PDF. Salida: {result.stdout} {result.stderr}')
            
            if not os.path.exists(final_path):
                raise Exception('El archivo PDF no fue creado')
            
            return final_path
            
        except FileNotFoundError:
            # Si LibreOffice no está disponible, solo copiar el archivo original
            ext = Path(excel_path).suffix
            original_name = Path(excel_path).stem
            unique_id = uuid.uuid4().hex[:12]
            new_filename = f"{unique_id}-{original_name}{ext}"
            output_path = os.path.join(self.processed_dir, new_filename)
            shutil.copy(excel_path, output_path)
            return output_path
        finally:
            # Limpiar directorio temporal
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
