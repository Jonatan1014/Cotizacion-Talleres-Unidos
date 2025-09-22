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
            $fileBase64 = '';
            $fileName = '';
            $fileSize = 0;
            $mimeType = '';
            
            if (file_exists($processedFilePath)) {
                $fileContent = file_get_contents($processedFilePath);
                $fileBase64 = base64_encode($fileContent);
                $fileName = basename($processedFilePath);
                $fileSize = filesize($processedFilePath);
                $mimeType = mime_content_type($processedFilePath);
            }

            // Preparar payload con ambos formatos
            $jsonData = [
                'original_file' => $data['original_file'],
                'processed_file' => $data['processed_file'],
                'file_type' => $data['file_type'],
                'timestamp' => $data['timestamp'],
                'file_info' => [
                    'name' => $fileName,
                    'size' => $fileSize,
                    'mime_type' => $mimeType,
                    'base64_content' => $fileBase64
                ]
            ];

            // Crear una solicitud multipart/form-data manualmente
            $boundary = '----WebKitFormBoundary' . uniqid();
            $postData = '';

            // Agregar datos JSON
            $postData .= "--{$boundary}\r\n";
            $postData .= "Content-Disposition: form-data; name=\"data\"\r\n";
            $postData .= "Content-Type: application/json\r\n\r\n";
            $postData .= json_encode($jsonData) . "\r\n";

            // Agregar archivo binario si existe
            if (!empty($fileContent)) {
                $postData .= "--{$boundary}\r\n";
                $postData .= "Content-Disposition: form-data; name=\"file\"; filename=\"{$fileName}\"\r\n";
                $postData .= "Content-Type: {$mimeType}\r\n\r\n";
                $postData .= $fileContent . "\r\n";
            }

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
            curl_close($ch);
            
            return [
                'success' => $httpCode >= 200 && $httpCode < 300,
                'http_code' => $httpCode,
                'response' => $response
            ];
            
        } catch (Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }
}
?>