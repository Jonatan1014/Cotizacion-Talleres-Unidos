# Copilot Instructions - Document Processing API

## Project Overview
This is a PHP-based document processing API that converts office documents (PDF, DOCX, XLSX, XLSM) and archives (ZIP, RAR) into standardized formats, then optionally forwards them to a webhook endpoint (typically n8n). The application runs in Docker with Apache/PHP 8.1 and uses system tools (LibreOffice, poppler-utils, p7zip) for conversions.

## Architecture & Data Flow

### Request Flow
1. **Entry Point**: `app/index.php` - Single routing controller with CORS headers enabled
2. **Controller**: `DocumentController` - Routes requests to service layer, handles multipart/binary uploads
3. **Service Layer**: `DocumentService` - Orchestrates upload, conversion, and webhook delivery
4. **Utilities**: `FileConverter` - Executes system commands for file transformations
5. **External Integration**: `WebhookService` - Sends processed files via multipart/form-data POST

### Key Directories
- `app/uploads/` - Temporary storage for uploaded files
- `app/uploads/processed/` - Converted output files (auto-created with 0755/0777 permissions)
- `/tmp/libreoffice_*` - Ephemeral directories for LibreOffice conversions (cleaned up after use)

## Critical Conversion Logic

### PDF Processing (`FileConverter::convertPdfToPng`)
- **Single-page PDFs**: Converts to PNG using `pdftoppm -png -f 1 -l 1`
- **Multi-page PDFs**: Copies original to `processed/` without conversion
- Uses `pdfinfo` to determine page count before deciding conversion path
- Output naming: `{uniqueId}-{originalName}.{ext}` (ensures no collisions)

### Office Document Conversions
Both DOCX and XLSX conversions use **LibreOffice in headless mode**:
```bash
HOME=/tmp timeout 60 xvfb-run --auto-servernum \
  libreoffice --headless --invisible --nodefault --nofirststartwizard \
  --nolockcheck --nologo --norestore --convert-to pdf \
  --outdir {tempDir} {inputFile}
```
- **Critical**: Files are copied to `/tmp/libreoffice_{uniqid}/` before conversion to avoid permission issues
- **Cleanup**: Temporary directories are removed via `rrmdir()` recursive deletion
- **Timeout**: 60-second limit prevents hanging conversions

### Archive Extraction (`DocumentService::extractArchive`)
Uses `wapmorgan/unified-archive` library to extract ZIP/RAR files:
- Extracts to permanent directory in `app/uploads/extracted_{uniqid}/`
- Returns **all extracted files without conversion or processing**
- No file type restrictions - extracts all files from archive
- Enforces 100MB limit for archive file size
- Returns detailed file metadata: name, path, relative_path, size, type, extension
- Controller sends extracted files as multipart/form-data with binary content
- Does NOT send files to webhook - only returns extraction results directly to client

## API Endpoints

### Standard Workflow Endpoints
- `POST /api/documents` - Upload + process + send to webhook (multipart)
- `POST /api/documents/bin` - Same as above, expects binary body with `X-Filename` header
- `POST /api/documents/transform` - Upload + process, returns converted file (multipart)
- `POST /api/documents/transform/bin` - Same, returns binary with `X-File-Name`/`X-File-Type` headers

### Archive Endpoints
- `POST /api/uploads-ziprar` - Extract ZIP/RAR and return all extracted files with binary content as multipart/form-data
- `POST /api/uploads-ziprar/bin` - Same as above, binary upload with `X-Filename` header
- **Important**: These endpoints return extracted files with their binary content in multipart format
- **Response Format**: multipart/form-data containing metadata and binary content for each extracted file

### Binary Upload Pattern
When `X-Filename` header is missing, system auto-detects extension via MIME type:
```php
$mimeType = (new finfo(FILEINFO_MIME_TYPE))->buffer($input);
$extensions = [
    'application/pdf' => '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document' => '.docx',
    // ...
];
```

## Environment Configuration

### Docker Environment Variables (docker-compose.yml)
- `WEBHOOK_URL` - Target endpoint for processed files (default: placeholder n8n URL)
- `UPLOAD_MAX_SIZE` - PHP upload limit (configured in `app/php.ini`)

### Webhook Integration
`WebhookService` sends multipart/form-data POST with:
- **Metadata fields**: `original_file`, `processed_file`, `file_type`, `timestamp`, `file_name`, `file_size`, `mime_type`
- **Binary field**: `file` - The actual processed file content
- **Custom boundary**: `----WebKitFormBoundary{uniqid()}`

## Development Patterns

### File Path Handling
- **Always use absolute paths** for file operations (see `DocumentService::processDocument`)
- File paths are used as document IDs in this implementation (no database)
- Processed files inherit source filename with unique prefix: `{uniqid()}-{originalName}.{newExt}`

### Error Handling Convention
Service methods return structured arrays:
```php
// Success
['success' => true, 'processed_file' => $path, 'message' => '...']

// Failure
['success' => false, 'message' => $errorMessage]
```

### Resource Cleanup Pattern
Use recursive directory removal after temporary operations:
```php
private function rrmdir($dir) {
    // Recursively delete directory contents, then directory itself
}
```
Applied after LibreOffice conversions and archive extractions.

## Dependencies

### System Tools (Dockerfile)
- `libreoffice` + `libreoffice-writer/calc` - Office document conversions
- `poppler-utils` (pdftoppm, pdfinfo) - PDF to image conversion
- `p7zip-full` - Archive extraction (ZIP/RAR via UnifiedArchive)
- `xvfb` - Virtual framebuffer for headless LibreOffice
- `ghostscript` - PDF processing support

### PHP Libraries (composer.json)
- `wapmorgan/unified-archive` - Multi-format archive handling (ZIP, RAR, 7z, etc.)

## Common Development Tasks

### Adding New File Type Support
1. Add extension to `$allowedTypes` in `DocumentService::uploadDocument`
2. Add conversion case in `DocumentService::processDocument` switch statement
3. Implement converter method in `FileConverter` (follow existing patterns)
4. Update Dockerfile if new system tools are required

### Testing Conversions Locally
```bash
# Enter running container
docker exec -it document-processor bash

# Test LibreOffice conversion manually
xvfb-run libreoffice --headless --convert-to pdf --outdir /tmp test.docx

# Test PDF info extraction
pdfinfo /path/to/file.pdf

# Check processed files
ls -la /var/www/html/app/uploads/processed/
```

### Debugging Webhook Failures
- Check `$this->webhookUrl` value in `WebhookService::sendToWebhook`
- Inspect curl response: `$response` and `$httpCode` in return array
- Verify n8n webhook accepts multipart/form-data with binary file field

## Project-Specific Conventions

1. **No Database**: File paths serve as document identifiers
2. **CORS Enabled**: Wide-open CORS policy in `index.php` for integration flexibility
3. **Dual Upload Modes**: All endpoints support both multipart and binary uploads
4. **Automatic Processing**: Default endpoints process immediately; `/transform` variants return files instead
5. **Archive Extraction**: `/uploads-ziprar` endpoints only extract, do NOT process or convert
6. **Stateless Design**: No session management; each request is independent

## Known Limitations

- 50MB file size limit for individual documents
- 100MB limit for archive files
- 60-second timeout on LibreOffice conversions
- No authentication/authorization mechanisms
- No database persistence (files are only storage)
- Processed files accumulate in `app/uploads/processed/` (no automatic cleanup)
