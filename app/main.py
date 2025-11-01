"""
API de Procesamiento de Documentos con FastAPI - Punto de Entrada Principal

API basada en Python/FastAPI que convierte documentos de office 
(PDF, DOCX, XLSX, XLSM) y archivos comprimidos (ZIP, RAR) a formatos estandarizados.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
import os

# Crear aplicación FastAPI
app = FastAPI(
    title="API de Procesamiento de Documentos",
    description="Conversión Automática de Documentos (PDF, DOCX, XLSX) y Extracción de Archivos (ZIP, RAR)",
    version="2.0.0"
)

# Configurar CORS - Política abierta para flexibilidad de integración
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
app.include_router(routes.router, prefix="/api")

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "API de Procesamiento de Documentos - Conversión Automática",
        "version": "2.0.0",
        "endpoints": [
            "POST /api/documents - Cargar y procesar documento automáticamente (multipart)",
            "POST /api/documents/bin - Cargar y procesar documento automáticamente (binario)",
            "POST /api/documents/transform - Transformar documento y devolver (multipart)",
            "POST /api/documents/transform/bin - Transformar documento y devolver (binario)",
            "GET /api/health - Verificación de salud",
            "POST /api/uploads-ziprar - Cargar y extraer .zip/.rar (multipart)",
            "POST /api/uploads-ziprar/bin - Cargar y extraer .zip/.rar (binario)"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Endpoint de verificación de salud"""
    from datetime import datetime
    return {
        "status": "saludable",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

# Asegurar que los directorios de carga existan
os.makedirs("app/uploads", exist_ok=True)
os.makedirs("app/uploads/processed", exist_ok=True)
