"""
Servicio de Documentos

Lógica principal para el procesamiento de documentos:
- Validación de carga
- Conversión de documentos (PDF, DOCX, XLSX)
- Extracción de archivos (ZIP, RAR)
"""

import os
import uuid
import shutil
import subprocess
import mimetypes
import base64
from datetime import datetime
from typing import Dict, Any, List, BinaryIO
from pathlib import Path
from pyunpack import Archive
from app.config import settings
from app.utils.file_converter import FileConverter
from app.models.schemas import DocumentInfo


class DocumentService:
    """Servicio para manejar carga, procesamiento y extracción de documentos"""
    
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.processed_dir = settings.processed_dir
        self.file_converter = FileConverter()
        
        # Asegurar que los directorios existan
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def upload_document(
        self,
        file_content: bytes,
        filename: str,
        already_saved: bool = False,
        saved_path: str = None
    ) -> Dict[str, Any]:
        """
        Cargar y validar documento.
        
        Args:
            file_content: Contenido binario del archivo
            filename: Nombre del archivo original
            already_saved: Si el archivo ya está guardado en disco
            saved_path: Ruta al archivo ya guardado
        
        Returns:
            Diccionario con estado de éxito, información del documento y mensaje
        """
        try:
            # Verificar tamaño del archivo
            file_size = len(file_content) if not already_saved else os.path.getsize(saved_path)
            if file_size > settings.upload_max_size:
                raise Exception(f'El tamaño del archivo excede el límite de {settings.upload_max_size // (1024*1024)}MB')
            
            # Validar tipo de archivo
            file_type = Path(filename).suffix.lower().lstrip('.')
            if file_type not in settings.allowed_document_types:
                raise Exception(
                    f'Tipo de archivo no permitido. Tipos permitidos: {", ".join(settings.allowed_document_types)}'
                )
            
            # Guardar archivo si no está guardado
            if not already_saved:
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(self.upload_dir, unique_filename)
                
                with open(file_path, 'wb') as f:
                    f.write(file_content)
            else:
                file_path = saved_path
            
            # Crear registro de documento
            document = DocumentInfo(
                original_name=filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                status='cargado',
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            return {
                'success': True,
                'document': document.model_dump(),
                'message': 'Documento cargado exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def process_document(self, document_path: str) -> Dict[str, Any]:
        """
        Procesar documento (convertir a formato destino).
        
        Args:
            document_path: Ruta absoluta al archivo de documento
        
        Returns:
            Diccionario con estado de éxito, ruta del archivo procesado
        """
        try:
            if not os.path.exists(document_path):
                raise Exception('Documento no encontrado')
            
            file_type = Path(document_path).suffix.lower().lstrip('.')
            processed_path = ''
            
            # Convertir según el tipo de archivo
            if file_type == 'pdf':
                processed_path = self.file_converter.convert_pdf_to_png(document_path)
            elif file_type == 'docx':
                processed_path = self.file_converter.convert_docx_to_pdf(document_path)
            elif file_type in ['xlsx', 'xlsm']:
                processed_path = self.file_converter.convert_excel_to_pdf(document_path)
            else:
                raise Exception('Tipo de archivo no soportado')
            
            # Verificar que el archivo procesado existe
            if not os.path.exists(processed_path):
                raise Exception(f'El archivo procesado no fue creado: {processed_path}')
            
            result = {
                'success': True,
                'processed_file': processed_path,
                'message': 'Documento procesado exitosamente'
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Obtener lista de todos los documentos cargados.
        
        Returns:
            Lista de diccionarios con metadatos de documentos
        """
        documents = []
        
        if not os.path.exists(self.upload_dir):
            return documents
        
        for file_path in Path(self.upload_dir).glob('*'):
            if file_path.is_file():
                documents.append({
                    'id': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'type': mimetypes.guess_type(str(file_path))[0] or 'desconocido',
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return documents
    
    def extract_archive(self, archive_path: str) -> Dict[str, Any]:
        """
        Extraer archivos de archivo ZIP o RAR.
        
        Args:
            archive_path: Ruta absoluta al archivo comprimido
        
        Returns:
            Diccionario con resultados de extracción y lista de archivos
        """
        try:
            if not os.path.exists(archive_path):
                raise Exception('Archivo no encontrado o no legible')
            
            # Crear directorio de extracción
            extract_dir = os.path.join(self.upload_dir, f'extracted_{uuid.uuid4().hex}')
            os.makedirs(extract_dir, exist_ok=True)
            
            try:
                # Detectar tipo de archivo
                ext = Path(archive_path).suffix.lower()
                
                if ext == '.rar':
                    # Usar unar para archivos RAR (mejor compatibilidad)
                    result = subprocess.run(
                        ['unar', '-no-directory', '-o', extract_dir, archive_path],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode != 0:
                        raise Exception(f'Error al extraer RAR: {result.stderr}')
                else:
                    # Usar pyunpack para otros formatos (ZIP, 7Z, etc.)
                    Archive(archive_path).extractall(extract_dir)
                    
            except FileNotFoundError as e:
                shutil.rmtree(extract_dir, ignore_errors=True)
                if 'unar' in str(e):
                    raise Exception(
                        'Para extraer archivos RAR necesitas instalar unar:\n'
                        'Linux: sudo apt-get install unar\n'
                        'macOS: brew install unar\n'
                        'Alternativamente, convierte el archivo a .zip que sí está soportado.'
                    )
                raise Exception(f'Herramienta de extracción no encontrada: {str(e)}')
            except Exception as e:
                shutil.rmtree(extract_dir, ignore_errors=True)
                error_msg = str(e)
                
                # Mensaje específico para archivos RAR con patool
                if 'patool' in error_msg.lower() and 'rar' in Path(archive_path).suffix.lower():
                    raise Exception(
                        'Error al extraer archivo RAR. Intenta con formato ZIP o verifica el archivo.'
                    )
                
                raise Exception(f'No se pudo extraer el archivo: {error_msg}')
            
            # Recolectar archivos extraídos
            extracted_files = []
            app_domain = settings.app_domain.rstrip('/')
            
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, extract_dir)
                    
                    # Construir ruta web para URL
                    web_path = os.path.relpath(file_path, 'app').replace('\\', '/')
                    file_url = f"{app_domain}/{web_path}"
                    
                    file_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                    extension = Path(file).suffix.lower().lstrip('.')
                    
                    # Leer contenido del archivo y codificar como base64
                    with open(file_path, 'rb') as f:
                        content = base64.b64encode(f.read()).decode('utf-8')
                    
                    extracted_files.append({
                        'name': file,
                        'path': file_path,
                        'relative_path': relative_path,
                        'url': file_url,
                        'size': os.path.getsize(file_path),
                        'type': file_type,
                        'extension': extension,
                        'content': content  # contenido binario codificado en base64
                    })
            
            if not extracted_files:
                shutil.rmtree(extract_dir, ignore_errors=True)
                raise Exception('No se extrajeron archivos del archivo comprimido')
            
            return {
                'success': True,
                'archive_path': archive_path,
                'extraction_dir': extract_dir,
                'extracted_count': len(extracted_files),
                'files': extracted_files,
                'message': f'Archivo extraído exitosamente. {len(extracted_files)} archivos extraídos.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Falló la extracción del archivo: {str(e)}'
            }
