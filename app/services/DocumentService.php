<?php
// app/services/DocumentService.php

// Incluir el autoloader de Composer para usar wapmorgan/UnifiedArchive
require_once __DIR__ . '/../../vendor/autoload.php'; // Ajusta la ruta si composer está en el root del proyecto
// require_once __DIR__ . '/../vendor/autoload.php'; // Alternativa si composer está en el directorio padre

require_once 'utils/FileConverter.php';
require_once 'services/WebhookService.php';
require_once 'models/Document.php';

use wapmorgan\UnifiedArchive\UnifiedArchive; // Importar la clase principal

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

            // Abrir el archivo con UnifiedArchive
            $archive = UnifiedArchive::open($archivePath);
            if ($archive === null) {
                throw new Exception('Could not open archive. Format might not be supported or file is corrupted.');
            }

            // Crear directorio temporal para extracción
            $tempDir = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'ua_extract_' . uniqid();
            if (!mkdir($tempDir, 0755, true) && !is_dir($tempDir)) {
                throw new Exception('Failed to create temp dir: ' . $tempDir);
            }

            // Opcional: Verificar espacio disponible antes de extraer
            $needed = $archive->getOriginalSize();
            $freeSpace = disk_free_space($tempDir);
            if ($freeSpace !== false && $needed > $freeSpace) {
                error_log("Warning: Estimated archive size ($needed) might exceed free space ($freeSpace) in $tempDir");
                // Puedes optar por lanzar un error aquí también si lo deseas estrictamente
                // throw new Exception('Not enough disk space to extract archive');
            }

            // Extraer archivos
            $extractedCount = $archive->extract($tempDir);

            // Tipos de archivos permitidos dentro del archivo
            $allowed = ['pdf', 'docx', 'xlsx', 'xlsm'];

            $processedFiles = [];
            $skippedFiles = []; // Para rastrear archivos omitidos

            // Iterar sobre los archivos extraídos
            $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($tempDir));
            foreach ($it as $file) {
                if ($file->isFile()) {
                    $ext = strtolower(pathinfo($file->getFilename(), PATHINFO_EXTENSION));
                    if (!in_array($ext, $allowed)) {
                        $skippedFiles[] = $file->getPathname();
                        continue; // Saltar archivos no permitidos
                    }

                    // Limitar tamaño de archivos individuales (ej. 50MB, como los otros uploads)
                    $fileSize = $file->getSize();
                    $maxFileSize = 50 * 1024 * 1024; // 50 MB
                    if ($fileSize > $maxFileSize) {
                        $skippedFiles[] = $file->getPathname();
                        continue; // Saltar archivos demasiado grandes
                    }

                    // Crear array tipo $_FILES para reutilizar uploadDocument
                    $fileInfo = [
                        'name' => $file->getFilename(),
                        'type' => mime_content_type($file->getPathname()),
                        'tmp_name' => $file->getPathname(),
                        'error' => 0,
                        'size' => $fileSize
                    ];

                    // Subir archivo (ya está guardado en temp), flag alreadySaved=true
                    $uploadResult = $this->uploadDocument($fileInfo, true);
                    if (!$uploadResult['success']) {
                        error_log("Error uploading extracted file: " . $file->getPathname() . " - " . $uploadResult['message']);
                        continue; // Saltar si falla la subida
                    }

                    // Procesar el archivo subido
                    $proc = $this->processDocument($uploadResult['document']['file_path']);
                    if ($proc['success']) {
                        $processedFiles[] = [
                            'original' => $uploadResult['document']['file_path'],
                            'processed' => $proc['processed_file']
                        ];
                    } else {
                        error_log("Error processing extracted file: " . $file->getPathname() . " - " . $proc['message']);
                        // Opcional: mover el archivo fallido a un directorio de errores o dejarlo
                    }
                }
            }

            // Limpiar directorio temporal
            $this->rrmdir($tempDir);

            return [
                'success' => true,
                'archive_path' => $archivePath,
                'extracted_count' => $extractedCount,
                'processed_files' => $processedFiles,
                'skipped_files' => $skippedFiles, // Incluir archivos omitidos en la respuesta
                'message' => 'Archive processed successfully. ' . count($processedFiles) . ' files processed, ' . count($skippedFiles) . ' skipped.'
            ];

        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Archive processing failed: ' . $e->getMessage()
            ];
        }
    }

    // Función auxiliar para eliminar directorios recursivamente
    private function rrmdir($dir) {
        if (is_dir($dir)) {
            $objects = scandir($dir);
            foreach ($objects as $object) {
                if ($object != "." && $object != "..") {
                    if (is_dir($dir . "/" . $object))
                        $this->rrmdir($dir . "/" . $object);
                    else
                        unlink($dir . "/" . $object);
                }
            }
            rmdir($dir);
        }
    }
}
?>