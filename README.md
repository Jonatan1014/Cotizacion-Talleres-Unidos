# 📄 API de Procesamiento de Documentos

API de alto rendimiento basada en Python/FastAPI para procesar documentos de oficina (PDF, DOCX, XLSX, XLSM) y extraer archivos comprimidos (ZIP, RAR) en formatos estandarizados.

## 🚀 Características

- **Conversión de Documentos**: Conversión automática de archivos PDF, DOCX, XLSX y XLSM
  - PDFs de una página → Imágenes PNG
  - PDFs multi-página → Preservados tal cual
  - DOCX/XLSX/XLSM → PDF usando LibreOffice en modo headless
  
- **Extracción de Archivos**: Extrae y procesa archivos ZIP/RAR
  - Devuelve todos los archivos con contenido codificado en base64
  - Genera URLs públicas para archivos extraídos
  
- **Dos Modos de Carga**: 
  - Cargas multipart/form-data
  - Cargas binarias con encabezado `X-Filename`
  
- **Modo Solo Transformación**: Procesa y devuelve archivos directamente
- **Soporte Docker**: Completamente containerizado con todas las dependencias del sistema

## 📋 Requisitos

### Con Docker (Recomendado)
- Docker 20.10+
- Docker Compose 1.29+

### Sin Docker (Windows/Linux)
- Python 3.11+
- LibreOffice (conversión de documentos)
- poppler-utils (procesamiento de PDF)
- 7-Zip o WinRAR (extracción de archivos)
- xvfb (solo Linux, servidor de display headless)

## 🐳 Instalación con Docker (Recomendado)

### Inicio Rápido

```bash
# 1. Clonar el repositorio
git clone <url-repositorio>
cd API-Analisis-Cotizacion

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Construir e iniciar con Docker Compose
docker-compose up --build -d

# 4. Verificar que esté corriendo
curl http://localhost:8000/api/health
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Documentación interactiva**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/health

### Usando Makefile (Linux/macOS)

```bash
# Ver todos los comandos disponibles
make help

# Despliegue completo (build + up + health check)
make deploy

# Ver logs en tiempo real
make logs

# Acceder al contenedor
make shell

# Detener
make down

# Limpiar todo
make clean
```

### Scripts de Despliegue

```bash
# Linux/macOS
chmod +x deploy.sh
./deploy.sh

# Windows PowerShell
docker-compose up --build -d
```

## 💻 Instalación Local (Sin Docker)

### Windows

**Nota**: En Windows necesitarás instalar herramientas adicionales. Docker es altamente recomendado.

1. **Instalar Python 3.11+**
   - Descarga desde: https://www.python.org/downloads/

2. **Instalar dependencias Python**
   ```bash
   pip install -r requirements.txt
   ```

3. **Instalar 7-Zip para soporte RAR**
   - Descarga desde: https://www.7-zip.org/
   - Agregar al PATH: `C:\Program Files\7-Zip\`

4. **Configurar variables de entorno**
   ```bash
   copy .env.example .env
   ```

5. **Iniciar el servidor**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

⚠️ **Importante**: En Windows, las conversiones de DOCX/XLSX/PDF pueden no funcionar sin LibreOffice y poppler-utils. Use Docker para funcionalidad completa.

Ver [INSTALACION_RAR.md](INSTALACION_RAR.md) para instrucciones detalladas sobre Windows.

### Linux (Ubuntu/Debian)

```bash
# 1. Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3-pip \
    libreoffice \
    poppler-utils \
    p7zip-full \
    unrar \
    xvfb \
    libmagic1

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Configurar entorno
cp .env.example .env

# 4. Crear directorios
mkdir -p app/uploads app/uploads/processed

# 5. Iniciar servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# Dominio de la aplicación (para generar URLs)
APP_DOMAIN=http://localhost:8000

# Límite de tamaño para documentos (bytes)
UPLOAD_MAX_SIZE=52428800  # 50MB

# Límite de tamaño para archivos comprimidos (bytes)
ARCHIVE_MAX_SIZE=104857600  # 100MB

# Timeout de conversión LibreOffice (segundos)
CONVERSION_TIMEOUT=60
```

## 📡 Endpoints de la API

### Procesamiento de Documentos

#### `POST /api/documents`
Cargar documento (multipart) y procesar automáticamente.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/documents" \
  -F "document=@archivo.pdf"
```

**Response:**
```json
{
  "success": true,
  "upload": {
    "original_name": "archivo.pdf",
    "file_path": "/app/app/uploads/abc123_archivo.pdf",
    "file_type": "pdf",
    "file_size": 1024000
  },
  "processing": {
    "processed_file": "/app/app/uploads/processed/abc123_archivo.png"
  },
  "message": "Documento cargado y procesado automáticamente"
}
```

#### `POST /api/documents/bin`
Cargar documento binario con encabezado `X-Filename`.

```bash
curl -X POST "http://localhost:8000/api/documents/bin" \
  -H "X-Filename: documento.docx" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@documento.docx"
```

### Transformación (Devolver Archivo)

#### `POST /api/documents/transform`
Transformar documento y devolver archivo procesado.

```bash
curl -X POST "http://localhost:8000/api/documents/transform" \
  -F "document=@archivo.xlsx" \
  -o resultado.pdf
```

#### `POST /api/documents/transform/bin`
Transformar documento binario y devolver archivo.

```bash
curl -X POST "http://localhost:8000/api/documents/transform/bin" \
  -H "X-Filename: documento.docx" \
  --data-binary "@documento.docx" \
  -o resultado.pdf
```

### Extracción de Archivos

#### `POST /api/uploads-ziprar`
Extraer archivos de ZIP/RAR (multipart).

```bash
curl -X POST "http://localhost:8000/api/uploads-ziprar" \
  -F "archive=@archivo.zip"
```

**Response:**
```json
{
  "success": true,
  "archive_path": "/app/app/uploads/archivo.zip",
  "extraction_dir": "/app/app/uploads/extracted_xyz789",
  "extracted_count": 3,
  "files": [
    {
      "name": "documento.pdf",
      "path": "/app/app/uploads/extracted_xyz789/documento.pdf",
      "size": 102400,
      "type": "application/pdf",
      "extension": "pdf",
      "url": "http://localhost:8000/uploads/extracted_xyz789/documento.pdf",
      "content": "JVBERi0xLjQKJeLjz9..."  // base64
    }
  ],
  "message": "Archivo extraído exitosamente. 3 archivos extraídos."
}
```

#### `POST /api/uploads-ziprar/bin`
Extraer archivos de ZIP/RAR (binario).

```bash
curl -X POST "http://localhost:8000/api/uploads-ziprar/bin" \
  -H "X-Filename: archivo.rar" \
  --data-binary "@archivo.rar"
```

### Utilidades

#### `GET /api/health`
Verificar estado de la API.

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "saludable",
  "timestamp": "2025-11-01T12:00:00",
  "version": "2.0.0"
}
```

#### `GET /api/documents`
Listar todos los documentos cargados.

```bash
curl http://localhost:8000/api/documents
```

## 📚 Documentación Interactiva

Una vez que el servidor esté corriendo, visita:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Comandos Docker Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar servidor
docker-compose restart

# Detener servidor
docker-compose down

# Reconstruir imagen
docker-compose build --no-cache
docker-compose up -d

# Acceder al contenedor
docker-compose exec app bash

# Ver estado de contenedores
docker-compose ps

# Limpiar volúmenes
docker-compose down -v
```

## 🧪 Pruebas

### Probar Conversión de PDF
```bash
curl -X POST "http://localhost:8000/api/documents/transform" \
  -F "document=@test.pdf" \
  -o resultado.png
```

### Probar Conversión de DOCX
```bash
curl -X POST "http://localhost:8000/api/documents/transform" \
  -F "document=@test.docx" \
  -o resultado.pdf
```

### Probar Extracción de RAR
```bash
curl -X POST "http://localhost:8000/api/uploads-ziprar" \
  -F "archive=@test.rar" \
  | python -m json.tool
```

## 🐛 Solución de Problemas

### Error al extraer archivos RAR

**Síntoma:**
```json
{
  "detail": "Falló la extracción del archivo: No se pudo extraer el archivo: patool not found!"
}
```

**Solución (Windows):**
1. Instala 7-Zip: https://www.7-zip.org/
2. Agrega `C:\Program Files\7-Zip\` al PATH
3. Reinicia la terminal

**Solución (Docker):**
El contenedor ya incluye todas las herramientas. Reconstruye la imagen:
```bash
docker-compose build --no-cache
docker-compose up -d
```

Ver [INSTALACION_RAR.md](INSTALACION_RAR.md) para más detalles.

### El servidor no inicia

```bash
# Ver logs detallados
docker-compose logs

# Verificar que el puerto 8000 esté libre
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/macOS
```

### Error de permisos en Linux

```bash
sudo chmod -R 777 app/uploads/
```

## 📁 Estructura del Proyecto

```
API-Analisis-Cotizacion/
├── app/
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── config.py               # Configuración global
│   ├── api/
│   │   └── routes.py           # Definición de endpoints
│   ├── models/
│   │   └── schemas.py          # Modelos Pydantic
│   ├── services/
│   │   └── document_service.py # Lógica de procesamiento
│   ├── utils/
│   │   └── file_converter.py   # Conversión de archivos
│   └── uploads/                # Archivos cargados
│       └── processed/          # Archivos procesados
├── Dockerfile                  # Imagen Docker
├── docker-compose.yml          # Orquestación Docker
├── requirements.txt            # Dependencias Python
├── .env.example                # Variables de entorno de ejemplo
├── start.sh                    # Script de inicio
├── deploy.sh                   # Script de despliegue
├── Makefile                    # Comandos make
├── README.md                   # Esta documentación
├── DOCKER.md                   # Guía detallada de Docker
└── INSTALACION_RAR.md          # Guía de instalación para RAR
```

## 🔒 Notas de Seguridad

- ✅ Los archivos se validan por tipo y tamaño
- ✅ Los nombres de archivo se sanitizan con UUIDs
- ⚠️ No hay autenticación por defecto (agregar según necesidad)
- ⚠️ CORS está abierto para desarrollo (restringir en producción)

### Recomendaciones para Producción

1. Agregar autenticación (JWT, API Keys, etc.)
2. Configurar CORS restrictivo
3. Usar HTTPS con certificados SSL
4. Limitar tasas de solicitud (rate limiting)
5. Monitorear logs y recursos

## 📖 Documentación Adicional

- [DOCKER.md](DOCKER.md) - Guía completa de Docker
- [INSTALACION_RAR.md](INSTALACION_RAR.md) - Instalación de herramientas RAR en Windows
- [MIGRATION.md](MIGRATION.md) - Notas de migración desde PHP

## 📝 Licencia

[Especificar licencia del proyecto]

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor abre un issue o pull request.

---

**Versión:** 2.0.0  
**Última actualización:** Noviembre 2025  
**Stack:** Python 3.11 + FastAPI + Docker
