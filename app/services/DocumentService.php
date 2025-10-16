<?php
require_once 'utils/FileConverter.php';
require_once 'services/WebhookService.php';
require_once 'models/Document.php';

class DocumentService {
    private $uploadDir;
    private $processedDir;
    private $fileConverter;
    private $webhookService;

    public function __construct() {
        $this->uploadDir = __DIR__ . '/../uploads/';
        $this->processedDir = __DIR__ . '/../uploads/processed/';
        $this->fileConverter = new FileConverter();
        $this->webhookService = new WebhookService();

        // Create directories if they don't exist
        if (!is_dir($this->uploadDir)) {
            mkdir($this->uploadDir, 0755, true);
        }
        if (!is_dir($this->processedDir)) {
            mkdir($this->processedDir, 0755, true);
        }
    }

    public function uploadDocument($file, $alreadySaved = false) {
        try {
            // Validate file
            if (!$alreadySaved && $file['error'] !== UPLOAD_ERR_OK) {
                throw new Exception('File upload error: ' . $file['error']);
            }

            // Check file size (50MB limit)
            $fileSize = $alreadySaved ? filesize($file['tmp_name']) : $file['size'];
            if ($fileSize > 50 * 1024 * 1024) {
                throw new Exception('File size exceeds 50MB limit');
            }

            // Get file info
            $fileName = $alreadySaved ? $file['name'] : $file['name'];
            $fileType = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));
            $allowedTypes = ['pdf', 'docx', 'xlsx', 'xlsm'];
            
            if (!in_array($fileType, $allowedTypes)) {
                throw new Exception('File type not allowed. Allowed types: ' . implode(', ', $allowedTypes));
            }

            $filePath = $alreadySaved ? $file['tmp_name'] : '';

            if (!$alreadySaved) {
                // Generate unique filename
                $filename = uniqid() . '_' . $file['name'];
                $filePath = $this->uploadDir . $filename;

                // Move uploaded file
                if (!move_uploaded_file($file['tmp_name'], $filePath)) {
                    throw new Exception('Failed to move uploaded file');
                }
            }

            // Create document record
            $document = new Document([
                'original_name' => $fileName,
                'file_path' => $filePath,
                'file_type' => $fileType,
                'file_size' => $fileSize,
                'status' => 'uploaded',
                'created_at' => date('Y-m-d H:i:s'),
                'updated_at' => date('Y-m-d H:i:s')
            ]);

            return [
                'success' => true,
                'document' => $document->toArray(),
                'message' => 'Document uploaded successfully'
            ];

        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => $e->getMessage()
            ];
        }
    }

    public function processDocument($documentId) {
        try {
            // For simplicity, we'll use the file path as ID
            // In a real application, you would query a database
            $filePath = $documentId;
            
            if (!file_exists($filePath)) {
                throw new Exception('Document not found');
            }

            $fileType = strtolower(pathinfo($filePath, PATHINFO_EXTENSION));
            $processedPath = '';

            switch ($fileType) {
                case 'pdf':
                    $processedPath = $this->fileConverter->convertPdfToPng($filePath);
                    break;
                case 'docx':
                    $processedPath = $this->fileConverter->convertDocxToPdf($filePath);
                    break;
                case 'xlsx':
                case 'xlsm':
                    $processedPath = $this->fileConverter->convertExcelToPdf($filePath);
                    break;
                default:
                    throw new Exception('Unsupported file type');
            }

            // Verificar que el archivo procesado exista
            if (!file_exists($processedPath)) {
                throw new Exception('Processed file was not created: ' . $processedPath);
            }

            // Send to webhook with absolute paths
            $webhookResult = $this->webhookService->sendToWebhook([
                'original_file' => $filePath,
                'processed_file' => $processedPath,
                'file_type' => $fileType,
                'timestamp' => date('Y-m-d H:i:s')
            ]);

            return [
                'success' => true,
                'processed_file' => $processedPath,
                'webhook_sent' => $webhookResult,
                'webhook_url' => $webhookResult['webhook_url'],
                'message' => 'Document processed successfully'
            ];

        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => $e->getMessage()
            ];
        }
    }

    // NUEVO MÉTODO: Procesar documento y devolver ruta del archivo transformado
    public function processDocumentForReturn($documentId) {
        try {
            // For simplicity, we'll use the file path as ID
            // In a real application, you would query a database
            $filePath = $documentId;
            
            if (!file_exists($filePath)) {
                throw new Exception('Document not found');
            }

            $fileType = strtolower(pathinfo($filePath, PATHINFO_EXTENSION));
            $processedPath = '';

            switch ($fileType) {
                case 'pdf':
                    $processedPath = $this->fileConverter->convertPdfToPng($filePath);
                    break;
                case 'docx':
                    $processedPath = $this->fileConverter->convertDocxToPdf($filePath);
                    break;
                case 'xlsx':
                case 'xlsm':
                    $processedPath = $this->fileConverter->convertExcelToPdf($filePath);
                    break;
                default:
                    throw new Exception('Unsupported file type');
            }

            // Verificar que el archivo procesado exista
            if (!file_exists($processedPath)) {
                throw new Exception('Processed file was not created: ' . $processedPath);
            }

            return [
                'success' => true,
                'processed_file' => $processedPath,
                'message' => 'Document processed successfully'
            ];

        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => $e->getMessage()
            ];
        }
    }

    public function getAllDocuments() {
        $documents = [];
        $files = glob($this->uploadDir . '*');
        
        foreach ($files as $file) {
            if (is_file($file)) {
                $documents[] = [
                    'id' => $file,
                    'name' => basename($file),
                    'size' => filesize($file),
                    'type' => mime_content_type($file),
                    'modified' => date('Y-m-d H:i:s', filemtime($file))
                ];
            }
        }
        
        return $documents;
    }

    // Nuevo: Procesar un archivo .zip o .rar: extraer y procesar los archivos internos
    public function processArchive($archivePath) {
        try {
            if (!file_exists($archivePath) || !is_readable($archivePath)) {
                throw new Exception('Archive not found or not readable');
            }

            // Space check: optional
            $tempDir = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'ua_extract_' . uniqid();
            if (!mkdir($tempDir, 0755, true) && !is_dir($tempDir)) {
                throw new Exception('Failed to create temp dir: ' . $tempDir);
            }

            // Use UnifiedArchive to open and extract
            $archive = \wapmorgan\UnifiedArchive\UnifiedArchive::open($archivePath);

            // Check extracted size vs free space
            $needed = $archive->getOriginalSize();
            if (disk_free_space($tempDir) !== false && disk_free_space($tempDir) < $needed) {
                // proceed but warn
                // throw new Exception('Not enough disk space to extract archive');
            }

            $extractedCount = $archive->extract($tempDir);

            // Allowed file types inside archive
            $allowed = ['pdf', 'docx', 'xlsx', 'xlsm'];

            $processedFiles = [];

            // Iterate extracted files
            $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($tempDir));
            foreach ($it as $file) {
                if ($file->isFile()) {
                    $ext = strtolower(pathinfo($file->getFilename(), PATHINFO_EXTENSION));
                    if (!in_array($ext, $allowed)) {
                        continue;
                    }

                    // Respect same size limits (100MB per file)
                    if ($file->getSize() > 100 * 1024 * 1024) {
                        continue; // skip too large files
                    }

                    // Build a fake $_FILES-like array to reuse uploadDocument
                    $fileInfo = [
                        'name' => $file->getFilename(),
                        'type' => mime_content_type($file->getPathname()),
                        'tmp_name' => $file->getPathname(),
                        'error' => 0,
                        'size' => $file->getSize()
                    ];

                    // Upload (already saved), so flag alreadySaved=true
                    $uploadResult = $this->uploadDocument($fileInfo, true);
                    if (!$uploadResult['success']) {
                        // Skip and continue
                        continue;
                    }

                    // Process the uploaded file
                    $proc = $this->processDocument($uploadResult['document']['file_path']);
                    if ($proc['success']) {
                        $processedFiles[] = [
                            'original' => $uploadResult['document']['file_path'],
                            'processed' => $proc['processed_file']
                        ];
                    }
                }
            }

            // Cleanup temp dir
            $this->rrmdir($tempDir);

            return [
                'success' => true,
                'extracted_count' => $extractedCount,
                'processed_files' => $processedFiles,
                'message' => 'Archive processed'
            ];

        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Archive processing failed: ' . $e->getMessage()
            ];
        }
    }
}
?>