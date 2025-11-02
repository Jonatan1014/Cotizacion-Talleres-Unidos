FROM ubuntu:22.04

# Configurar timezone y evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Bogota

# Instalar Python y dependencias del sistema
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    ca-certificates \
    curl \
    fonts-dejavu-core \
    fonts-liberation \
    ghostscript \
    libicu-dev \
    libmagic1 \
    libssl1.1 \
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear enlaces simbólicos para Python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

COPY app/ ./app/
COPY .env .env

RUN mkdir -p /app/app/uploads /app/app/uploads/processed /tmp/libreoffice && \
    chmod -R 777 /app/app/uploads /tmp

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV HOME=/tmp
ENV PYTHONPATH=/app
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300", "--workers", "2"]