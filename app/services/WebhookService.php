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
            
            if (file_exists($processedFilePath)) {
                $fileContent = file_get_contents($processedFilePath);
                $fileBase64 = base64_encode($fileContent);
            }

            // Preparar payload con contenido base64
            $payloadData = [
                'original_file' => $data['original_file'],
                'processed_file' => $data['processed_file'],
                'file_type' => $data['file_type'],
                'timestamp' => $data['timestamp'],
                'file_content_base64' => $fileBase64,
                'file_name' => basename($data['processed_file'])
            ];

            $payload = json_encode($payloadData);
            
            $ch = curl_init($this->webhookUrl);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Content-Length: ' . strlen($payload)
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