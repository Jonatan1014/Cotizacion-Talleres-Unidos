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

            // Asegurar que el nombre tenga el formato ID-nombre_original.ext
            $processedPath = $this->ensureCorrectFileName($processedPath, $filePath);

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

    // Método para asegurar el nombre correcto del archivo
    private function ensureCorrectFileName($processedPath, $originalPath) {
        $processedName = basename($processedPath);
        
        // Si el nombre ya tiene el formato ID-nombre.ext, usarlo tal cual
        if (preg_match('/^\d+-/', $processedName)) {
            return $processedPath;
        }
        
        // Obtener el nombre original sin extensión
        $originalNameWithoutExt = pathinfo(basename($originalPath), PATHINFO_FILENAME);
        
        // Generar ID único
        $uniqueId = uniqid();
        
        // Crear nuevo nombre: ID-OriginalName.ext
        $newFileName = $uniqueId . '-' . $originalNameWithoutExt . '.' . pathinfo($processedName, PATHINFO_EXTENSION);
        
        // Renombrar el archivo
        $newPath = dirname($processedPath) . '/' . $newFileName;
        if (rename($processedPath, $newPath)) {
            return $newPath;
        }
        
        return $processedPath;
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
}
?>