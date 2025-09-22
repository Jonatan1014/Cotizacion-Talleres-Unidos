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

    public function uploadDocument($file) {
        try {
            // Validate file
            if ($file['error'] !== UPLOAD_ERR_OK) {
                throw new Exception('File upload error: ' . $file['error']);
            }

            // Check file size (50MB limit)
            if ($file['size'] > 50 * 1024 * 1024) {
                throw new Exception('File size exceeds 50MB limit');
            }

            // Get file info
            $fileType = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
            $allowedTypes = ['pdf', 'docx', 'xlsx', 'xlsm'];
            
            if (!in_array($fileType, $allowedTypes)) {
                throw new Exception('File type not allowed. Allowed types: ' . implode(', ', $allowedTypes));
            }

            // Generate unique filename
            $filename = uniqid() . '_' . $file['name'];
            $filePath = $this->uploadDir . $filename;

            // Move uploaded file
            if (!move_uploaded_file($file['tmp_name'], $filePath)) {
                throw new Exception('Failed to move uploaded file');
            }

            // Create document record
            $document = new Document([
                'original_name' => $file['name'],
                'file_path' => $filePath,
                'file_type' => $fileType,
                'file_size' => $file['size'],
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

            // Limpiar las rutas usando el método correcto
            $cleanOriginalPath = $this->normalizePath($filePath);
            $cleanProcessedPath = $this->normalizePath($processedPath);

            // Send to webhook
            $webhookResult = $this->webhookService->sendToWebhook([
                'original_file' => $cleanOriginalPath,
                'processed_file' => $cleanProcessedPath,
                'file_type' => $fileType,
                'timestamp' => date('Y-m-d H:i:s')
            ]);

            return [
                'success' => true,
                'processed_file' => $cleanProcessedPath,
                'webhook_sent' => $webhookResult,
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

    private function normalizePath($path) {
        // Convertir a ruta relativa limpia
        $path = str_replace('\\', '/', $path); // Normalizar barras
        $path = preg_replace('/\/+/', '/', $path); // Eliminar barras dobles
        
        // Convertir rutas absolutas a relativas si es necesario
        if (strpos($path, '/var/www/html/') === 0) {
            $path = substr($path, strlen('/var/www/html/'));
        }
        
        // Eliminar .. redundantes
        $pathParts = explode('/', $path);
        $newPathParts = [];
        
        foreach ($pathParts as $part) {
            if ($part === '..') {
                array_pop($newPathParts);
            } elseif ($part !== '' && $part !== '.') {
                $newPathParts[] = $part;
            }
        }
        
        return '/' . implode('/', $newPathParts);
    }
}
?>