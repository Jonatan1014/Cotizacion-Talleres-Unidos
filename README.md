# File Conversion API

API REST para conversión de archivos construida con FastAPI. Soporta conversión de imágenes, documentos y audio.

## 🚀 Características

- **Conversión de Imágenes**: JPG, PNG, GIF, BMP, WebP, TIFF, ICO → múltiples formatos
- **Conversión de Documentos**: PDF, DOCX, DOC, XLSX, TXT, HTML → PDF, DOCX, TXT, HTML
- **Conversión de Audio**: MP3, WAV, OGG, FLAC, AAC, M4A → múltiples formatos
- **⚡ Smart Conversion**: Auto-detección y conversión inteligente de archivos
  - Word (.doc, .docx) → PDF
  - Excel (.xls, .xlsx) → PDF
  - PDF (1 página) → JPG
  - PDF (múltiples páginas) → Se devuelve sin modificar
- **API RESTful** con documentación automática (Swagger/OpenAPI)
- **Arquitectura escalable** con patrón Factory y servicios modulares
- **Docker ready** para fácil despliegue

## 📁 Estructura del Proyecto

```
app/
├── __init__.py
├── main.py                    # Punto de entrada de la aplicación
├── config/
│   └── settings.py            # Configuración y variables de entorno
├── api/
│   └── v1/
│       ├── router.py          # Router principal v1
│       └── endpoints/
│           ├── conversion.py  # Endpoints de conversión
│           ├── health.py      # Health checks
│           ├── formats.py     # Formatos soportados
│           └── smart.py       # Conversión inteligente
├── core/
│   ├── exceptions.py          # Excepciones personalizadas
│   └── middleware.py          # Middleware (logging, rate limit)
├── models/
│   └── schemas.py             # Modelos Pydantic
├── services/
│   ├── base_converter.py      # Clase base abstracta
│   ├── converter_factory.py   # Factory para convertidores
│   ├── conversion_service.py  # Servicio principal
│   ├── smart_converter.py     # Convertidor inteligente
│   └── converters/
│       ├── image_converter.py
│       ├── document_converter.py
│       └── audio_converter.py
└── utils/
    ├── file_handler.py        # Utilidades de archivos
    └── validators.py          # Validadores
```

## 🛠 Instalación

### Con Docker (Recomendado)

```bash
# Construir y ejecutar
docker-compose up --build

# Solo construir
docker-compose build

# Ejecutar en background
docker-compose up -d
```

### Sin Docker

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Dependencias del sistema (Ubuntu/Debian)
sudo apt-get install libmagic1 ffmpeg libreoffice poppler-utils ghostscript

# Ejecutar
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Endpoints

### Health Check
- `GET /api/v1/health` - Estado del servicio
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### Conversión Manual
- `POST /api/v1/conversion/convert` - Convertir archivo
- `GET /api/v1/conversion/download/{job_id}` - Descargar archivo convertido
- `DELETE /api/v1/conversion/cleanup/{job_id}` - Limpiar archivos del job
- `POST /api/v1/conversion/validate` - Validar si una conversión es soportada

### ⚡ Smart Conversion (Auto-detección)
- `POST /api/v1/smart/process` - **Procesar archivo automáticamente** (devuelve el archivo convertido)
- `POST /api/v1/smart/process/stream` - Versión streaming para archivos grandes
- `POST /api/v1/smart/detect` - Detectar tipo de archivo sin convertir
- `GET /api/v1/smart/supported-types` - Listar tipos soportados y sus conversiones

### Formatos
- `GET /api/v1/formats` - Listar todos los formatos soportados
- `GET /api/v1/formats/{category}` - Formatos por categoría
- `GET /api/v1/formats/output/{input_format}` - Formatos de salida disponibles

## 📖 Documentación

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 Configuración

Copia `.env.example` a `.env` y ajusta las variables:

```env
APP_NAME=File Conversion API
DEBUG=false
MAX_FILE_SIZE=52428800  # 50 MB
IMAGE_QUALITY=85
```

## 📦 Uso

### ⚡ Smart Conversion (Recomendado)

El endpoint `/api/v1/smart/process` detecta automáticamente el tipo de archivo y lo convierte:

```bash
# Word a PDF
curl -X POST "http://localhost:8000/api/v1/smart/process" \
  -F "file=@documento.docx" \
  --output documento.pdf

# Excel a PDF
curl -X POST "http://localhost:8000/api/v1/smart/process" \
  -F "file=@hoja.xlsx" \
  --output hoja.pdf

# PDF (1 página) a JPG
curl -X POST "http://localhost:8000/api/v1/smart/process" \
  -F "file=@factura.pdf" \
  --output factura.jpg

# Detectar tipo sin convertir
curl -X POST "http://localhost:8000/api/v1/smart/detect" \
  -F "file=@archivo.docx"
```

### Conversión Manual

#### Convertir una imagen a PNG

```bash
curl -X POST "http://localhost:8000/api/v1/conversion/convert" \
  -F "file=@imagen.jpg" \
  -F "target_format=png" \
  -F "quality=90"
```

#### Convertir con resize

```bash
curl -X POST "http://localhost:8000/api/v1/conversion/convert" \
  -F "file=@imagen.jpg" \
  -F "target_format=webp" \
  -F "width=800"
```

### Convertir audio

```bash
curl -X POST "http://localhost:8000/api/v1/conversion/convert" \
  -F "file=@audio.wav" \
  -F "target_format=mp3" \
  -F "bitrate=320k"
```

## 🧪 Tests

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/
```

## 📄 Licencia

MIT License
