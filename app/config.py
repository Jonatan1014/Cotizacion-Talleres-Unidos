"""
Gestión de configuración para la API de Procesamiento de Documentos
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno"""
    
    # Dominio de la aplicación para generar URLs de archivos
    app_domain: str = "http://localhost:8000"
    
    # Límites de carga
    upload_max_size: int = 50 * 1024 * 1024  # 50MB para documentos
    archive_max_size: int = 100 * 1024 * 1024  # 100MB para archivos comprimidos
    
    # Rutas de archivos
    upload_dir: str = "app/uploads/"
    processed_dir: str = "app/uploads/processed/"
    
    # Tipos de archivo permitidos
    allowed_document_types: list = ["pdf", "docx", "xlsx", "xlsm"]
    allowed_archive_types: list = ["zip", "rar"]
    
    # Timeout de conversión de LibreOffice (segundos)
    conversion_timeout: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()
