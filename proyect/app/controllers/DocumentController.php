<?php
require_once 'services/DocumentService.php';
require_once 'services/WebhookService.php';

class DocumentController {
    private $documentService;
    private $webhookService;
    
    public function __construct() {
        $this->documentService = new DocumentService();
        $this->webhookService = new WebhookService();
    }
    
    public function processDocument($file) {
        // Validar archivo
        $validation = $this->validateFile($file);
        if (!$validation['valid']) {
            throw new Exception($validation['message']);
        }
        
        // Guardar archivo temporalmente
        $uploadResult = $this->uploadFile($file);
        if (!$uploadResult['success']) {
            throw new Exception('Failed to upload file');
        }
        
        $filePath = $uploadResult['path'];
        $fileName = $uploadResult['name'];
        $fileExtension = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));
        
        try {
            // Procesar documento según tipo
            $processedFile = $this->documentService->processDocument($filePath, $fileExtension);
            
            // Enviar a webhook
            $webhookResult = $this->webhookService->sendToWebhook([
                'original_file' => $fileName,
                'processed_file' => basename($processedFile),
                'file_path' => $processedFile,
                'timestamp' => date('Y-m-d H:i:s')
            ]);
            
            // Limpiar archivos temporales (opcional)
            // $this->cleanupFiles([$filePath, $processedFile]);
            
            return [
                'success' => true,
                'message' => 'Document processed successfully',
                'original_file' => $fileName,
                'processed_file' => basename($processedFile),
                'webhook_sent' => $webhookResult
            ];
            
        } catch (Exception $e) {
            // Limpiar archivos en caso de error
            $this->cleanupFiles([$filePath]);
            throw $e;
        }
    }
    
    private function validateFile($file) {
        $maxFileSize = getenv('MAX_FILE_SIZE') ?: 10485760; // 10MB default
        
        if ($file['error'] !== UPLOAD_ERR_OK) {
            return ['valid' => false, 'message' => 'File upload error'];
        }
        
        if ($file['size'] > $maxFileSize) {
            return ['valid' => false, 'message' => 'File too large'];
        }
        
        $allowedExtensions = ['pdf', 'docx', 'xlsx', 'xlsm'];
        $extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        
        if (!in_array($extension, $allowedExtensions)) {
            return ['valid' => false, 'message' => 'File type not supported'];
        }
        
        return ['valid' => true];
    }
    
    private function uploadFile($file) {
        $uploadDir = __DIR__ . '/../uploads/';
        if (!is_dir($uploadDir)) {
            mkdir($uploadDir, 0755, true);
        }
        
        $fileName = uniqid() . '_' . basename($file['name']);
        $targetPath = $uploadDir . $fileName;
        
        if (move_uploaded_file($file['tmp_name'], $targetPath)) {
            return [
                'success' => true,
                'path' => $targetPath,
                'name' => $fileName
            ];
        }
        
        return ['success' => false];
    }
    
    private function cleanupFiles($files) {
        foreach ($files as $file) {
            if (file_exists($file)) {
                unlink($file);
            }
        }
    }
}
?>