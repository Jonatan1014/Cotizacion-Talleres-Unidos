<?php
class WebhookService {
    private $webhookUrl;

    public function __construct() {
        $this->webhookUrl = getenv('WEBHOOK_URL') ?: 'https://your-n8n-webhook-url.com/webhook';
    }

    public function sendToWebhook($data) {
        try {
            // Leer el contenido del archivo procesado
            $processedFilePath = $data['processed_file'];
            $fileContent = '';
            $fileName = '';
            $fileSize = 0;
            $mimeType = '';
            
            if (file_exists($processedFilePath)) {
                $fileContent = file_get_contents($processedFilePath);
                $fileName = basename($processedFilePath);
                $fileSize = filesize($processedFilePath);
                $mimeType = mime_content_type($processedFilePath);
            } else {
                throw new Exception('Processed file not found: ' . $processedFilePath);
            }

            // Crear una solicitud multipart/form-data con solo el archivo binario
            $boundary = '----WebKitFormBoundary' . uniqid();
            $postData = '';

            // Agregar metadatos como campos individuales
            $metadata = [
                'original_file' => $data['original_file'],
                'processed_file' => $data['processed_file'],
                'file_type' => $data['file_type'],
                'timestamp' => $data['timestamp'],
                'file_name' => $fileName,
                'file_size' => $fileSize,
                'mime_type' => $mimeType
            ];

            foreach ($metadata as $key => $value) {
                $postData .= "--{$boundary}\r\n";
                $postData .= "Content-Disposition: form-data; name=\"{$key}\"\r\n\r\n";
                $postData .= "{$value}\r\n";
            }

            // Agregar archivo binario
            $postData .= "--{$boundary}\r\n";
            $postData .= "Content-Disposition: form-data; name=\"file\"; filename=\"{$fileName}\"\r\n";
            $postData .= "Content-Type: {$mimeType}\r\n\r\n";
            $postData .= $fileContent . "\r\n";

            $postData .= "--{$boundary}--\r\n";

            $ch = curl_init($this->webhookUrl);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: multipart/form-data; boundary=' . $boundary,
                'Content-Length: ' . strlen($postData)
            ]);
            
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $error = curl_error($ch);
            curl_close($ch);
            
            if ($error) {
                throw new Exception('cURL Error: ' . $error);
            }
            
            return [
                'success' => $httpCode >= 200 && $httpCode < 300,
                'http_code' => $httpCode,
                'response' => $response,
                'webhook_url' => $this->webhookUrl  // ← Añadido

            ];
            
        } catch (Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'webhook_url' => $this->webhookUrl  // ← Añadido

            ];
        }
    }
}
?>