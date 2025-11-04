# Dockerfile - API de Procesamiento de Documentos con FastAPI
FROM python:3.11-slim

# Instalar dependencias del sistema para conversión de documentos
# unrar-free: Necesario para rarfile (extracción de archivos RAR)
RUN apt-get update && apt-get install -y \
    curl \
    fonts-dejavu-core \
    fonts-liberation \
    ghostscript \
    libmagic1 \
    libreoffice \
    libreoffice-calc \
    libreoffice-common \
    libreoffice-core \
    libreoffice-writer \
    p7zip-full \
    poppler-utils \
    unrar-free \
    unzip \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivo de requisitos
COPY requirements.txt .

# Instalar dependencias de Python con timeout extendido
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

# Copiar archivos de la aplicación
COPY app/ ./app/
COPY .env .env

# Crear directorios de carga con permisos apropiados
RUN mkdir -p /app/app/uploads /app/app/uploads/processed /tmp/libreoffice && \
    chmod -R 777 /app/app/uploads /tmp

# Exponer puerto para FastAPI
EXPOSE 8000

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1
ENV HOME=/tmp
ENV PYTHONPATH=/app

# Ejecutar FastAPI con uvicorn (SIN --reload en producción)
# Aumentar timeout a 300 segundos y usar 2 workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300", "--workers", "2"]