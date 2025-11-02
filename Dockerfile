# Dockerfile - API de Procesamiento de Documentos con FastAPI
FROM python:3.11-slim

# Instalar dependencias del sistema para conversión de documentos
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    fonts-dejavu-core \
    fonts-liberation \
    ghostscript \
    libicu-dev \
    libmagic1 \
    libreoffice \
    libreoffice-calc \
    libreoffice-common \
    libreoffice-core \
    libreoffice-writer \
    p7zip-full \
    poppler-utils \
    unar \
    unzip \
    xvfb \
    gcc \
    g++ \
    python3-dev \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar OpenSSL 1.1 manualmente (compatible con aspose-zip)
RUN wget http://security.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.23_amd64.deb && \
    dpkg -i libssl1.1_1.1.1f-1ubuntu2.23_amd64.deb && \
    rm libssl1.1_1.1.1f-1ubuntu2.23_amd64.deb

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
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Ejecutar FastAPI con uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300", "--workers", "2"]