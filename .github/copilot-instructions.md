# Copilot Instructions - Document Processing API (FastAPI)

## Project Overview
This is a **Python/FastAPI-based** document processing API that converts office documents (PDF, DOCX, XLSX, XLSM) and archives (ZIP, RAR) into standardized formats, then optionally forwards them to a webhook endpoint (typically n8n). The application runs in Docker with Python 3.11, FastAPI, and uses system tools (LibreOffice, poppler-utils, p7zip) for conversions.

## Architecture & Data Flow

### Request Flow
1. **Entry Point**: `app/main.py` - FastAPI application with CORS middleware
2. **Routes**: `app/api/routes.py` - Endpoint handlers for multipart/binary uploads
3. **Service Layer**: `app/services/document_service.py` - Orchestrates upload, conversion, and webhook delivery
4. **Utilities**: `app/utils/file_converter.py` - Executes system commands for file transformations
5. **External Integration**: `app/services/webhook_service.py` - Sends processed files via multipart/form-data POST using httpx

### Key Directories
- `app/uploads/` - Temporary storage for uploaded files
- `app/uploads/processed/` - Converted output files (auto-created with proper permissions)
- `/tmp/libreoffice_*` - Ephemeral directories for LibreOffice conversions (cleaned up after use)

## Critical Conversion Logic

### PDF Processing (`FileConverter.convert_pdf_to_png`)
- **Single-page PDFs**: Converts to PNG using `pdftoppm -png -f 1 -l 1`
- **Multi-page PDFs**: Copies original to `processed/` without conversion
- Uses `pdfinfo` subprocess to determine page count before deciding conversion path
- Output naming: `{uniqueId}-{originalName}.{ext}` (ensures no collisions)

### Office Document Conversions
Both DOCX and XLSX conversions use **LibreOffice in headless mode** via subprocess:
```python
subprocess.run([
    'timeout', '60',
    'xvfb-run', '--auto-servernum', '--server-args=-screen 0 1024x768x24',
    'libreoffice', '--headless', '--invisible', '--nodefault',
    '--nofirststartwizard', '--nolockcheck', '--nologo', '--norestore',
    '--convert-to', 'pdf', '--outdir', temp_dir, temp_file
], env={'HOME': '/tmp'}, timeout=60)
```
- **Critical**: Files are copied to `/tmp/libreoffice_{uuid}/` before conversion to avoid permission issues
- **Cleanup**: Temporary directories are removed via `shutil.rmtree()` 
- **Timeout**: 60-second limit prevents hanging conversions

### Archive Extraction (`DocumentService.extract_archive`)
Uses `pyunpack` library (wrapper for patool) to extract ZIP/RAR files:
- Extracts to permanent directory in `app/uploads/extracted_{uuid}/`
- Returns **all extracted files without conversion or processing**
- No file type restrictions - extracts all files from archive
- Enforces 100MB limit for archive file size
- Returns detailed file metadata: name, path, relative_path, url, size, type, extension, **content** (base64)
- **URL generation**: Uses `APP_DOMAIN` environment variable from `app/config.py` settings
- Endpoints return extracted files as JSON with base64-encoded binary content
- Does NOT send files to webhook - only returns extraction results directly to client

## API Endpoints

### Standard Workflow Endpoints
- `POST /api/documents` - Upload + process + send to webhook (multipart) - **Async handler**
- `POST /api/documents/bin` - Same as above, expects binary body with `X-Filename` header
- `POST /api/documents/transform` - Upload + process, returns converted file (multipart)
- `POST /api/documents/transform/bin` - Same, returns binary with `X-File-Name`/`X-File-Type` headers

### Archive Endpoints
- `POST /api/uploads-ziprar` - Extract ZIP/RAR and return all files with binary content encoded in base64
- `POST /api/uploads-ziprar/bin` - Same as above, binary upload with `X-Filename` header
- **Important**: These endpoints return JSON with each file's metadata and base64-encoded binary content
- **Response Format**: JSON with `files` array where each file includes `content` field with base64 data

### Binary Upload Pattern
When `X-Filename` header is missing, system auto-detects extension via MIME type using `python-magic`:
```python
import magic
mime = magic.Magic(mime=True)
mime_type = mime.from_buffer(content)
extension_map = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    # ...
}
```

## Environment Configuration

### Docker Environment Variables (docker-compose.yml & .env)
- `WEBHOOK_URL` - Target endpoint for processed files (default: placeholder n8n URL)
- `UPLOAD_MAX_SIZE` - Document upload limit in bytes (50MB default)
- `ARCHIVE_MAX_SIZE` - Archive upload limit in bytes (100MB default)
- `APP_DOMAIN` - Public domain URL for generating file URLs (e.g., `http://localhost:8000`)

### Configuration Management (`app/config.py`)
Uses Pydantic Settings for environment variable management:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    webhook_url: str = "https://your-n8n-webhook-url.com/webhook"
    app_domain: str = "http://localhost:8000"
    upload_max_size: int = 50 * 1024 * 1024
    # ...
    class Config:
        env_file = ".env"

settings = Settings()  # Global instance
```

### Webhook Integration
`WebhookService` sends multipart/form-data POST using **httpx.AsyncClient**:
- **Metadata fields**: `original_file`, `processed_file`, `file_type`, `timestamp`, `file_name`, `file_size`, `mime_type`
- **Binary field**: `file` - The actual processed file content
- **Async operation**: Uses `async with httpx.AsyncClient()` for non-blocking I/O

## Development Patterns

### Async/Await Convention
All route handlers are `async def` functions:
```python
@router.post("/documents")
async def upload_and_process_document(document: UploadFile = File(...)):
    content = await document.read()  # Async file read
    result = await document_service.process_document(path, send_webhook=True)
    # ...
```

### File Path Handling
- **Always use absolute paths** with `os.path.join()` or `Path`
- File paths are used as document IDs (no database)
- Processed files inherit source filename with unique prefix: `{uuid}-{originalName}.{newExt}`

### Error Handling Convention
Service methods return dictionaries (typed with Pydantic models):
```python
# Success
{'success': True, 'processed_file': path, 'message': '...'}

# Failure
{'success': False, 'message': error_message}

# FastAPI routes convert to HTTPException
if not result['success']:
    raise HTTPException(status_code=400, detail=result['message'])
```

### Resource Cleanup Pattern
Use `shutil.rmtree()` for recursive directory removal:
```python
try:
    # ... processing ...
finally:
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
```

## Dependencies

### System Tools (Dockerfile)
- `libreoffice` + `libreoffice-writer/calc` - Office document conversions
- `poppler-utils` (pdftoppm, pdfinfo) - PDF to image conversion
- `p7zip-full` - Archive extraction (via pyunpack)
- `xvfb` - Virtual framebuffer for headless LibreOffice
- `ghostscript` - PDF processing support
- `libmagic1` - MIME type detection for python-magic

### Python Libraries (requirements.txt)
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `python-multipart` - Multipart form data support
- `httpx` - Async HTTP client for webhook calls
- `pydantic` + `pydantic-settings` - Data validation and settings management
- `python-magic` - MIME type detection
- `pyunpack` + `patool` - Multi-format archive handling

## Common Development Tasks

### Adding New File Type Support
1. Add extension to `allowed_document_types` in `app/config.py` Settings
2. Add conversion case in `DocumentService.process_document()` switch logic
3. Implement converter method in `FileConverter` class (follow existing patterns)
4. Update Dockerfile if new system tools are required

### Testing Conversions Locally
```bash
# Enter running container
docker exec -it document-processor-fastapi bash

# Test LibreOffice conversion manually
xvfb-run libreoffice --headless --convert-to pdf --outdir /tmp test.docx

# Test PDF info extraction
pdfinfo /path/to/file.pdf

# Check processed files
ls -la /app/app/uploads/processed/
```

### Running the Application Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export WEBHOOK_URL="https://webhook.com/endpoint"
export APP_DOMAIN="http://localhost:8000"

# Run with auto-reload (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run with Docker
docker-compose up --build
```

### Debugging Webhook Failures
- Check `self.webhook_url` value in `WebhookService.send_to_webhook`
- Inspect response: `response.status_code` and `response.text` 
- Verify n8n webhook accepts multipart/form-data with binary file field
- Use `async with httpx.AsyncClient()` for debugging async issues

## Project-Specific Conventions

1. **No Database**: File paths serve as document identifiers
2. **CORS Enabled**: Wide-open CORS policy via FastAPI middleware for integration flexibility
3. **Dual Upload Modes**: All endpoints support both multipart and binary uploads
4. **Automatic Processing**: Default endpoints process immediately; `/transform` variants return files instead
5. **Archive Extraction**: `/uploads-ziprar` endpoints only extract, do NOT process or convert
6. **Stateless Design**: No session management; each request is independent
7. **Async by Default**: Use `async def` for all route handlers and service methods that do I/O
8. **Type Annotations**: Use Pydantic models for request/response validation

## FastAPI-Specific Patterns

### Dependency Injection
Service instances are created at module level:
```python
document_service = DocumentService()

@router.post("/documents")
async def handler(document: UploadFile = File(...)):
    result = document_service.upload_document(...)
```

### Response Models
Use Pydantic models for automatic OpenAPI schema generation:
```python
@router.post("/documents", response_model=DocumentProcessResponse)
async def upload_and_process_document(...):
    return {
        'success': True,
        'upload': {...},
        'processing': {...}
    }
```

### File Handling
- `UploadFile` for multipart uploads: `await document.read()`
- `Request.body()` for binary uploads: `await request.body()`
- `FileResponse` for returning files
- `Response` for custom binary responses with headers

## Known Limitations

- 50MB file size limit for individual documents
- 100MB limit for archive files
- 60-second timeout on LibreOffice conversions
- No authentication/authorization mechanisms
- No database persistence (files are only storage)
- Processed files accumulate in `app/uploads/processed/` (no automatic cleanup)
- Synchronous file I/O in some places (SonarQube warnings - acceptable for this use case)

## Migration Notes (PHP → Python)

This codebase was migrated from PHP to Python/FastAPI while maintaining the same API contract:
- **Same endpoints**: All routes preserved for backward compatibility
- **Same logic**: Conversion workflows remain identical
- **Performance improvements**: Async/await for better concurrency
- **Type safety**: Pydantic models replace manual validation
- **Modern tooling**: FastAPI auto-generates OpenAPI docs at `/docs`

