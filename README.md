# 📄 Sistema de Procesamiento de Documentos y Análisis con IA

## 🎯 Descripción General

Este sistema es una solución integral de **procesamiento automático de documentos** diseñada para una empresa metalmecánica. Combina una API REST en PHP para la conversión de formatos de documentos con un workflow automatizado de n8n que analiza documentos técnicos mediante inteligencia artificial para generar **resúmenes ejecutivos** de cotizaciones.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    FLUJO GENERAL DEL SISTEMA                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   📧 Gmail ──▶ 🤖 n8n ──▶ 📤 API Convert ──▶ 🔄 OCR/IA ──▶ 📝 Informe       │
│                                                                              │
│   1. Recepción de correos con documentos adjuntos                           │
│   2. Clasificación de intención (¿Es cotización?)                           │
│   3. Conversión de formatos (PDF/DOCX/XLSX → PNG/PDF)                       │
│   4. Análisis OCR con Mistral AI                                            │
│   5. Análisis de imágenes con OpenAI/GPT-4                                  │
│   6. Generación de resumen ejecutivo con Grok-4                             │
│   7. Almacenamiento en Google Drive y notificación                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
Cotizacion-Talleres-Unidos/
│
├── 🐳 Docker
│   ├── Dockerfile              # Imagen PHP 8.1 + Apache + LibreOffice + Poppler
│   └── docker-compose.yml      # Orquestación de servicios
│
├── 📁 app/
│   ├── index.php               # Punto de entrada API (Router)
│   ├── php.ini                 # Configuración PHP
│   │
│   ├── 📂 controllers/
│   │   └── DocumentController.php    # Controlador principal
│   │
│   ├── 📂 services/
│   │   ├── DocumentService.php       # Lógica de negocio
│   │   └── WebhookService.php        # Comunicación con n8n
│   │
│   ├── 📂 utils/
│   │   └── FileConverter.php         # Conversiones de archivos
│   │
│   ├── 📂 models/
│   │   └── Document.php              # Modelo de datos
│   │
│   └── 📂 uploads/                   # Almacenamiento de archivos
│       └── processed/                # Archivos convertidos
│
├── 📁 logs/                          # Logs de Apache
│
└── 📋 Pruebas Talleres Funcionando V2.json   # Workflow n8n exportado
```

---

## 🌐 API REST - Endpoints de Conversión

### Base URL
```
https://convert-format.systemautomatic.xyz
```

### 📋 Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Información de la API y endpoints disponibles |
| `GET` | `/api/health` | Estado de salud del servicio |
| `POST` | `/api/documents` | Subir y procesar documento (multipart) |
| `POST` | `/api/documents/bin` | Subir y procesar documento (binario) |
| `POST` | `/api/documents/transform` | Transformar y devolver documento (multipart) |
| `POST` | `/api/documents/transform/bin` | Transformar y devolver documento (binario) |
| `GET` | `/api/documents` | Listar todos los documentos |

---

### 📤 POST `/api/documents` - Subir y Procesar (Multipart)

Sube un documento, lo convierte y **envía el resultado a un webhook de n8n**.

#### Request
```bash
curl -X POST https://convert-format.systemautomatic.xyz/api/documents \
  -F "document=@cotizacion.pdf"
```

#### Response (200 OK)
```json
{
  "success": true,
  "upload": {
    "original_name": "cotizacion.pdf",
    "file_path": "/var/www/html/uploads/6789abc_cotizacion.pdf",
    "file_type": "pdf",
    "file_size": 1024567,
    "status": "uploaded",
    "created_at": "2026-01-29 10:30:00"
  },
  "processing": {
    "processed_file": "/var/www/html/uploads/processed/6789abc-cotizacion.png",
    "webhook_sent": {
      "success": true,
      "http_code": 200
    }
  },
  "webhook_url": "https://your-n8n-webhook-url.com/webhook",
  "message": "Document uploaded, processed and sent to webhook automatically"
}
```

---

### 📤 POST `/api/documents/bin` - Subir y Procesar (Binario)

Similar al anterior pero recibe el archivo como **cuerpo binario** del request.

#### Request
```bash
curl -X POST https://convert-format.systemautomatic.xyz/api/documents/bin \
  -H "X-Filename: cotizacion.pdf" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @cotizacion.pdf
```

#### Headers Opcionales
| Header | Descripción |
|--------|-------------|
| `X-Filename` | Nombre del archivo (si no se proporciona, se genera automáticamente) |

---

### 🔄 POST `/api/documents/transform` - Transformar y Devolver (Multipart)

Sube un documento, lo convierte y **devuelve el archivo convertido directamente**.

#### Request
```bash
curl -X POST https://convert-format.systemautomatic.xyz/api/documents/transform \
  -F "document=@plano.pdf" \
  -o plano_convertido.png
```

#### Response
- **Content-Type**: `image/png` o `application/pdf`
- **Content-Disposition**: `attachment; filename="converted_file.png"`
- **Body**: Archivo binario convertido

---

### 🔄 POST `/api/documents/transform/bin` - Transformar y Devolver (Binario)

**Endpoint más utilizado por n8n**. Recibe binario y devuelve binario.

#### Request
```bash
curl -X POST https://convert-format.systemautomatic.xyz/api/documents/transform/bin \
  -H "X-Filename: documento.xlsx" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @documento.xlsx \
  -o documento_convertido.pdf
```

#### Response Headers
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="6789abc-documento.pdf"
X-File-Name: 6789abc-documento.pdf
X-File-Type: application/pdf
```

---

## 🔄 Proceso de Conversión de Documentos

### Flujo de Transformación

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FLUJO DE CONVERSIÓN                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📄 PDF (1 página)  ─────────────▶  🖼️ PNG                             │
│        │                                                                │
│        └─ (múltiples páginas) ───▶  📄 PDF (copia sin cambios)         │
│                                                                         │
│  📝 DOCX ────────────────────────▶  📄 PDF                             │
│                                                                         │
│  📊 XLSX / XLSM ─────────────────▶  📄 PDF                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Detalle Técnico de Conversiones

#### PDF → PNG (1 página)
```php
// Usa poppler-utils (pdftoppm)
$command = "pdftoppm -png -f 1 -l 1 {$pdfPath} {$outputPrefix}";
```

#### PDF → PDF (múltiples páginas)
Los PDFs con más de una página se copian tal cual al directorio de procesados, manteniendo el formato original.

#### DOCX → PDF
```php
// Usa LibreOffice en modo headless con xvfb
$command = "HOME=/tmp timeout 60 xvfb-run --auto-servernum libreoffice 
            --headless --convert-to pdf --outdir {$tempDir} {$docxPath}";
```

#### XLSX/XLSM → PDF
```php
// Mismo proceso que DOCX
$command = "HOME=/tmp timeout 60 xvfb-run --auto-servernum libreoffice 
            --headless --convert-to pdf --outdir {$tempDir} {$excelPath}";
```

---

## 📤 Sistema de Webhook

Cuando se usa `/api/documents` o `/api/documents/bin`, el archivo procesado se envía automáticamente a un webhook configurado mediante la variable de entorno `WEBHOOK_URL`.

### Datos Enviados al Webhook

```
┌──────────────────────────────────────────────────────────────────┐
│                  PAYLOAD MULTIPART/FORM-DATA                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Campos de Metadatos:                                            │
│  ├── original_file    → Ruta del archivo original               │
│  ├── processed_file   → Ruta del archivo procesado              │
│  ├── file_type        → Tipo de archivo (pdf, docx, xlsx)       │
│  ├── timestamp        → Fecha y hora de procesamiento           │
│  ├── file_name        → Nombre del archivo procesado            │
│  ├── file_size        → Tamaño en bytes                         │
│  └── mime_type        → Tipo MIME del archivo                   │
│                                                                  │
│  Archivo Binario:                                                │
│  └── file             → Contenido binario del archivo           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Workflow de n8n - Análisis Inteligente de Documentos

El archivo `Pruebas Talleres Funcionando V2.json` contiene un workflow completo para automatizar el análisis de cotizaciones.

### 📊 Diagrama del Workflow

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    WORKFLOW n8n                                            │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                            │
│  📧 Gmail Trigger                                                                          │
│       │ (cada minuto)                                                                      │
│       ▼                                                                                    │
│  🤖 DeepSeek AI ─────────────────────▶ ¿Cotizar?                                          │
│       │ (Análisis de intención)              │                                             │
│       │                              ┌───────┴───────┐                                     │
│       │                              │               │                                     │
│       │                             Sí              No ──▶ FIN                            │
│       │                              │                                                     │
│       ▼                              ▼                                                     │
│  📥 Obtener mensaje completo con adjuntos                                                 │
│       │                                                                                    │
│       ▼                                                                                    │
│  📎 ¿Tiene Documentos? ─────────────────────────────┐                                     │
│       │                                              │                                     │
│      Sí                                             No ──▶ FIN                            │
│       │                                                                                    │
│       ▼                                                                                    │
│  📂 Crear carpeta en Google Drive                                                         │
│       │  (Cotizacion_{Asunto}_{Remitente})                                                │
│       │                                                                                    │
│       ├──▶ 📝 Crear documento Google Docs (datos crudos)                                  │
│       │                                                                                    │
│       └──▶ 📝 Crear documento "Informe Ejecutivo"                                         │
│                  │                                                                         │
│                  ▼                                                                         │
│  🔄 Por cada archivo adjunto:                                                             │
│       │                                                                                    │
│       ├──▶ 💾 Subir a carpeta del proyecto                                               │
│       │                                                                                    │
│       ├──▶ ⬇️ Descargar archivo                                                          │
│       │                                                                                    │
│       └──▶ 📤 Enviar a API Convert (/api/documents/transform/bin)                        │
│                  │                                                                         │
│                  ▼                                                                         │
│            ┌─────┴─────┐                                                                  │
│            │           │                                                                   │
│          PNG?        PDF?                                                                  │
│            │           │                                                                   │
│            ▼           ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐                      │
│  │              ANÁLISIS CON MISTRAL OCR                           │                      │
│  │  1. Subir archivo a Mistral Files API                          │                      │
│  │  2. Obtener URL del documento                                   │                      │
│  │  3. Ejecutar OCR con mistral-ocr-latest                        │                      │
│  │  4. Extraer texto markdown + imágenes base64                   │                      │
│  └─────────────────────────────────────────────────────────────────┘                      │
│                  │                                                                         │
│                  ▼                                                                         │
│            ¿PDF tiene imágenes?                                                           │
│                  │                                                                         │
│       ┌──────────┴──────────┐                                                             │
│       │                     │                                                              │
│      Sí                    No                                                              │
│       │                     │                                                              │
│       ▼                     ▼                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                                                │
│  │   OpenAI GPT-4  │  │  Solo texto OCR │                                                │
│  │   Vision        │  │                 │                                                │
│  │   (Análisis de  │  └─────────────────┘                                                │
│  │    planos)      │           │                                                          │
│  └─────────────────┘           │                                                          │
│       │                        │                                                          │
│       └────────────┬───────────┘                                                          │
│                    ▼                                                                       │
│  📝 Actualizar documento Google Docs con info extraída                                    │
│                    │                                                                       │
│                    ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐                      │
│  │           GENERADOR DE INFORME EJECUTIVO                        │                      │
│  │                     (Grok-4 Fast)                               │                      │
│  │                                                                 │                      │
│  │  Analiza 8 secciones:                                          │                      │
│  │  1. Términos y Condiciones Legales del Contrato                │                      │
│  │  2. Términos Tributarios                                       │                      │
│  │  3. Términos de Fabricación Normativa ASME                     │                      │
│  │  4. Términos de Calidad                                        │                      │
│  │  5. Términos de Transporte de Equipos                          │                      │
│  │  6. Términos de Entrega y Facturación                          │                      │
│  │  7. Términos de Seguridad Industrial y Salud Ocupacional       │                      │
│  │  8. Términos de Relación Comunitaria                           │                      │
│  └─────────────────────────────────────────────────────────────────┘                      │
│                    │                                                                       │
│                    ▼                                                                       │
│  📄 Guardar en documento "Informe Ejecutivo" en Google Docs                               │
│                    │                                                                       │
│                    ▼                                                                       │
│  📧 Enviar correo con informe adjunto                                                     │
│                    │                                                                       │
│                    ▼                                                                       │
│  📲 Notificar por Telegram                                                                │
│                                                                                            │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 🔧 Nodos Principales del Workflow

#### 1. **Gmail Trigger** 📧
- Consulta cada minuto nuevos correos
- Descarga información del mensaje (asunto, cuerpo, remitente)

#### 2. **Análisis de Intención** 🤖
- **Modelo**: DeepSeek
- **Temperatura**: 0.1 (respuestas consistentes)
- **Objetivo**: Clasificar correos en "Cotizar" u "Otro"
- **Prompt del sistema**:
```
Clasificar con precisión la intención de correos electrónicos 
para una empresa metalmecánica.
- "Cotizar": Solicitud de cotización
- "Otro": Cualquier otra cosa
```

#### 3. **Conversión de Documentos** 🔄
- Envía cada archivo adjunto a `/api/documents/transform/bin`
- Recibe el documento convertido (PNG para PDFs de 1 página, PDF para otros)

#### 4. **Mistral OCR** 📖
- Sube archivos a Mistral Files API
- Extrae texto en formato Markdown
- Incluye imágenes en base64 si las hay

#### 5. **OpenAI GPT-4 Vision** 👁️
- Analiza imágenes de planos industriales
- Extrae:
  - Componentes principales
  - Materiales específicos
  - Medidas críticas
  - Proceso de fabricación propuesto
  - Pruebas técnicas requeridas

#### 6. **Generador de Informe** 📝
- **Modelo**: Grok-4 Fast (via OpenRouter)
- **Temperatura**: 0.1
- Genera resumen ejecutivo estructurado en 8 secciones

---

## 🐳 Configuración Docker

### Dockerfile
```dockerfile
FROM php:8.1-apache

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    libzip-dev libpng-dev libjpeg-dev libfreetype6-dev \
    ghostscript libreoffice libreoffice-core libreoffice-common \
    libreoffice-writer libreoffice-calc poppler-utils xvfb

# Extensiones PHP
RUN docker-php-ext-install -j$(nproc) gd zip pdo_mysql

# Configuración
RUN a2enmod rewrite
EXPOSE 80
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  app:
    build: .
    container_name: document-processor
    ports:
      - "80:80"
    volumes:
      - ./app:/var/www/html
      - ./logs:/var/log/apache2
    environment:
      - WEBHOOK_URL=${WEBHOOK_URL}
      - UPLOAD_MAX_SIZE=${UPLOAD_MAX_SIZE}
    restart: unless-stopped
```

### Variables de Entorno
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `WEBHOOK_URL` | URL del webhook de n8n | `https://n8n.ejemplo.com/webhook/xxx` |
| `UPLOAD_MAX_SIZE` | Tamaño máximo de archivos | `50M` |

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Convertir PDF a PNG
```bash
# Enviar un PDF de 1 página
curl -X POST https://convert-format.systemautomatic.xyz/api/documents/transform \
  -F "document=@plano_tecnico.pdf" \
  -o plano_tecnico.png

# Resultado: archivo PNG descargado
```

### Ejemplo 2: Convertir Excel a PDF
```bash
# Enviar un archivo Excel
curl -X POST https://convert-format.systemautomatic.xyz/api/documents/transform/bin \
  -H "X-Filename: cotizacion.xlsx" \
  --data-binary @cotizacion.xlsx \
  -o cotizacion.pdf

# Resultado: archivo PDF descargado
```

### Ejemplo 3: Procesar y Enviar a Webhook
```bash
# El archivo se convierte y se envía a n8n automáticamente
curl -X POST https://convert-format.systemautomatic.xyz/api/documents \
  -F "document=@especificaciones.docx"

# Response:
# {
#   "success": true,
#   "processing": { "webhook_sent": { "success": true } },
#   "message": "Document uploaded, processed and sent to webhook automatically"
# }
```

---

## ⚠️ Limitaciones del Sistema

### API de Conversión

| Limitación | Detalle |
|------------|---------|
| **Tamaño máximo de archivo** | 50 MB por documento |
| **Formatos soportados** | Solo PDF, DOCX, XLSX, XLSM |
| **PDFs escaneados** | No se optimizan, solo se copian si tienen múltiples páginas |
| **Timeout de conversión** | 60 segundos para LibreOffice |
| **Sin persistencia de base de datos** | Los documentos usan el sistema de archivos |
| **Concurrencia** | LibreOffice puede tener problemas con múltiples conversiones simultáneas |

### Workflow de n8n

| Limitación | Detalle |
|------------|---------|
| **Polling de Gmail** | Solo revisa cada 1 minuto |
| **Análisis de imágenes** | Modelo GPT-4 Vision con `detail: low` para reducir costos |
| **Dependencia de APIs externas** | Mistral, OpenAI, OpenRouter, Google APIs |
| **Sin reintentos automáticos** | Si falla un nodo, puede perder información |
| **Idioma** | Optimizado para español |
| **Contexto ASME** | Especializado en equipos metalmecánicos bajo normativa ASME |

### OCR y Análisis

| Limitación | Detalle |
|------------|---------|
| **Calidad de OCR** | Depende de la calidad del documento original |
| **Planos muy complejos** | El análisis de imágenes puede no captar todos los detalles |
| **Documentos protegidos** | No puede procesar PDFs con contraseña |
| **Tablas complejas** | El OCR puede tener dificultades con tablas anidadas |

---

## � API Keys y Cuentas Requeridas

Para el funcionamiento completo del sistema, necesitas configurar las siguientes cuentas y obtener sus respectivas API Keys:

### 📊 Resumen de Servicios Necesarios

| Servicio | Propósito | Tipo de Autenticación | Costo Aproximado |
|----------|-----------|----------------------|------------------|
| **Google Cloud** | Gmail, Drive, Docs, Sheets | OAuth 2.0 | Gratis (límites generosos) |
| **DeepSeek** | Clasificación de intención | API Key | ~$0.14/millón tokens |
| **Mistral AI** | OCR de documentos | API Key | ~$0.15/1000 páginas |
| **OpenAI** | Análisis de imágenes (GPT-4 Vision) | API Key | ~$0.01-0.03/imagen |
| **OpenRouter** | Grok-4 para informes ejecutivos | API Key | Variable según modelo |
| **Telegram** | Notificaciones | Bot Token | Gratis |

---

### 🔵 1. Google Cloud Platform (Gmail, Drive, Docs, Sheets)

#### Cuentas Necesarias
- Una cuenta de Google con acceso a Gmail, Drive y Docs

#### Configuración OAuth 2.0

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PASOS PARA GOOGLE OAUTH 2.0                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Ir a Google Cloud Console (console.cloud.google.com)               │
│  2. Crear nuevo proyecto o seleccionar existente                       │
│  3. Habilitar APIs:                                                    │
│     ├── Gmail API                                                      │
│     ├── Google Drive API                                               │
│     ├── Google Docs API                                                │
│     └── Google Sheets API                                              │
│  4. Configurar pantalla de consentimiento OAuth                        │
│  5. Crear credenciales OAuth 2.0 (Aplicación web)                      │
│  6. Agregar URI de redirección de n8n:                                 │
│     └── https://tu-n8n.com/rest/oauth2-credential/callback             │
│  7. Copiar Client ID y Client Secret                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Configuración en n8n
1. Ir a **Credentials** → **New Credential**
2. Buscar "Gmail OAuth2" / "Google Drive OAuth2" / "Google Docs OAuth2"
3. Pegar Client ID y Client Secret
4. Hacer clic en **Sign in with Google** y autorizar

#### Permisos (Scopes) Requeridos
```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/spreadsheets
```

---

### 🟣 2. DeepSeek API (Análisis de Intención)

#### Obtener API Key
1. Ir a [platform.deepseek.com](https://platform.deepseek.com)
2. Crear cuenta o iniciar sesión
3. Ir a **API Keys** → **Create new secret key**
4. Copiar la API Key generada

#### Configuración en n8n
1. Ir a **Credentials** → **New Credential**
2. Buscar "DeepSeek"
3. Pegar la API Key

#### Uso en el Workflow
- **Modelo utilizado**: `deepseek-chat`
- **Temperatura**: 0.1 (respuestas consistentes)
- **Propósito**: Clasificar correos como "Cotizar" o "Otro"

#### Ejemplo de Costo
```
Prompt de clasificación: ~100 tokens
Por cada 10,000 correos: ~$0.14
```

---

### 🟠 3. Mistral AI (OCR de Documentos)

#### Obtener API Key
1. Ir a [console.mistral.ai](https://console.mistral.ai)
2. Crear cuenta o iniciar sesión
3. Ir a **API Keys** → **Create new key**
4. Copiar la API Key

#### Configuración en n8n
1. Ir a **Credentials** → **New Credential**
2. Buscar "HTTP Header Auth"
3. Configurar:
   - **Name**: `Authorization`
   - **Value**: `Bearer tu_api_key_aqui`

#### APIs Utilizadas en el Workflow
```
POST https://api.mistral.ai/v1/files      → Subir documento
GET  https://api.mistral.ai/v1/files/{id}/url → Obtener URL temporal
POST https://api.mistral.ai/v1/ocr        → Ejecutar OCR
```

#### Modelo OCR
- **Modelo**: `mistral-ocr-latest`
- **Incluye**: Extracción de texto en Markdown + imágenes en base64

#### Ejemplo de Costo
```
Documento de 5 páginas: ~$0.00075
Por cada 1,000 documentos: ~$0.15
```

---

### 🟢 4. OpenAI API (GPT-4 Vision)

#### Obtener API Key
1. Ir a [platform.openai.com](https://platform.openai.com)
2. Crear cuenta o iniciar sesión
3. Ir a **API Keys** → **Create new secret key**
4. Copiar la API Key

#### Configuración en n8n
1. Ir a **Credentials** → **New Credential**
2. Buscar "OpenAI API"
3. Pegar la API Key

#### Uso en el Workflow
- **Modelo**: `gpt-4.1-2025-04-14` (GPT-4 Vision)
- **Detalle de imagen**: `low` (reduce costos)
- **Max tokens**: 2000
- **Propósito**: Analizar planos industriales y diagramas técnicos

#### Prompt de Análisis de Imágenes
```
Análisis técnico de planos industriales:
- Componentes principales
- Materiales específicos
- Medidas críticas
- Proceso de fabricación propuesto
- Pruebas técnicas requeridas
```

#### Ejemplo de Costo
```
Imagen con detail:low: ~$0.00085
Por cada 100 imágenes analizadas: ~$0.085
```

---

### 🔴 5. OpenRouter API (Grok-4 para Informes)

#### Obtener API Key
1. Ir a [openrouter.ai](https://openrouter.ai)
2. Crear cuenta (puedes usar Google/GitHub)
3. Ir a **Keys** → **Create Key**
4. Copiar la API Key

#### Configuración en n8n
1. Ir a **Credentials** → **New Credential**
2. Buscar "OpenRouter"
3. Pegar la API Key

#### Modelo Utilizado
- **Modelo**: `x-ai/grok-4-fast`
- **Temperatura**: 0.1
- **Propósito**: Generar resúmenes ejecutivos estructurados

#### ¿Por qué Grok-4 via OpenRouter?
```
┌─────────────────────────────────────────────────────────────────────────┐
│  OpenRouter permite acceder a múltiples LLMs con una sola API Key:     │
│                                                                         │
│  • Grok-4 (xAI) - Rápido y efectivo para análisis                      │
│  • Claude (Anthropic) - Alternativa para textos largos                 │
│  • Llama 3 (Meta) - Opción económica                                   │
│  • GPT-4 (OpenAI) - Cuando se necesita máxima calidad                  │
│                                                                         │
│  Ventaja: Puedes cambiar de modelo sin reconfigurar credenciales       │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Ejemplo de Costo
```
Informe ejecutivo (~2000 tokens output): ~$0.02-0.05
Por cada 100 informes: ~$2-5
```

---

### 🔵 6. Telegram Bot (Notificaciones)

#### Crear Bot de Telegram
1. Abrir Telegram y buscar `@BotFather`
2. Enviar `/newbot`
3. Seguir las instrucciones para nombrar el bot
4. Copiar el **Bot Token** proporcionado

#### Obtener Chat ID
1. Enviar un mensaje a tu bot
2. Visitar: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
3. Buscar el `chat.id` en la respuesta JSON

#### Configuración en n8n
1. Ir a **Credentials** → **New Credential**
2. Buscar "Telegram API"
3. Pegar el Bot Token
4. En el nodo de Telegram, configurar el Chat ID

#### Uso en el Workflow
- Envía notificación cuando se completa el análisis de una cotización

---

### 📋 Resumen de Configuración en n8n

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CREDENCIALES A CONFIGURAR EN n8n                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Credentials → New Credential:                                          │
│                                                                         │
│  1. 📧 Gmail OAuth2                                                     │
│     └── Client ID + Client Secret de Google Cloud                      │
│                                                                         │
│  2. 📁 Google Drive OAuth2                                              │
│     └── Mismas credenciales de Google Cloud                            │
│                                                                         │
│  3. 📝 Google Docs OAuth2                                               │
│     └── Mismas credenciales de Google Cloud                            │
│                                                                         │
│  4. 📊 Google Sheets OAuth2                                             │
│     └── Mismas credenciales de Google Cloud                            │
│                                                                         │
│  5. 🤖 DeepSeek API                                                     │
│     └── API Key de platform.deepseek.com                               │
│                                                                         │
│  6. 🔤 HTTP Header Auth (para Mistral)                                  │
│     └── Header: Authorization                                          │
│     └── Value: Bearer sk-xxx                                           │
│                                                                         │
│  7. 🧠 OpenAI API                                                       │
│     └── API Key de platform.openai.com                                 │
│                                                                         │
│  8. 🌐 OpenRouter API                                                   │
│     └── API Key de openrouter.ai                                       │
│                                                                         │
│  9. 📲 Telegram API                                                     │
│     └── Bot Token de @BotFather                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 💰 Estimación de Costos Mensuales

| Volumen de Trabajo | Costo Estimado/Mes |
|-------------------|-------------------|
| **Bajo** (50 cotizaciones/mes) | ~$2-5 |
| **Medio** (200 cotizaciones/mes) | ~$8-15 |
| **Alto** (500+ cotizaciones/mes) | ~$20-40 |

> **Nota**: Los servicios de Google (Gmail, Drive, Docs) son gratuitos dentro de los límites estándar. El costo principal viene de las APIs de IA (Mistral, OpenAI, OpenRouter).

---

### 🔒 Buenas Prácticas de Seguridad

1. **Nunca commitear API Keys** en repositorios públicos
2. **Usar variables de entorno** para las credenciales
3. **Rotar API Keys** periódicamente
4. **Configurar límites de gasto** en cada plataforma:
   - OpenAI: Settings → Billing → Usage limits
   - OpenRouter: Settings → Limits
   - Mistral: Console → Billing → Limits
5. **Revisar logs regularmente** para detectar uso anómalo

---

## �🚀 Despliegue

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd Cotizacion-Talleres-Unidos
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus valores
```

### 3. Construir y ejecutar
```bash
docker-compose up -d --build
```

### 4. Importar workflow en n8n
1. Abrir n8n
2. Ir a Workflows → Import from file
3. Seleccionar `Pruebas Talleres Funcionando V2.json`
4. Configurar credenciales:
   - Gmail OAuth2
   - Google Drive OAuth2
   - Google Docs OAuth2
   - DeepSeek API
   - Mistral API
   - OpenAI API
   - OpenRouter API
   - Telegram Bot

### 5. Verificar funcionamiento
```bash
curl https://convert-format.systemautomatic.xyz/api/health
# {"status":"healthy","timestamp":"2026-01-29 10:00:00","version":"1.0.0"}
```

---

## 📞 Soporte

Para problemas técnicos, revisar:
- **Logs de Apache**: `/logs/`
- **Logs de n8n**: Panel de ejecuciones del workflow
- **Estado de la API**: `GET /api/health`

---

## 📝 Licencia

Proyecto privado - Talleres Unidos
