<?php
use GuzzleHttp\Client;

class WebhookService {
    private $client;
    private $webhookUrl;
    
    public function __construct() {
        $this->client = new Client();
        $this->webhookUrl = getenv('WEBHOOK_URL') ?: 'http://localhost:5678/webhook';
    }
    
    public function sendToWebhook($data) {
        try {
            $response = $this->client->post($this->webhookUrl, [
                'json' => $data,
                'timeout' => 30
            ]);
            
            return [
                'success' => true,
                'status_code' => $response->getStatusCode(),
                'response' => (string) $response->getBody()
            ];
            
        } catch (Exception $e) {
            error_log("Webhook error: " . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }
}
?>