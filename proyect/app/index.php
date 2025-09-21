<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once 'vendor/autoload.php';

// Rutas
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];

try {
    switch ($uri) {
        case '/api/health':
            handleHealthCheck();
            break;
            
        case '/api/documents/upload':
            if ($method === 'POST') {
                handleDocumentUpload();
            } else {
                sendResponse(405, ['error' => 'Method not allowed']);
            }
            break;
            
        case '/api/documents/status':
            if ($method === 'GET') {
                handleStatusCheck();
            } else {
                sendResponse(405, ['error' => 'Method not allowed']);
            }
            break;
            
        default:
            sendResponse(404, ['error' => 'Endpoint not found']);
            break;
    }
} catch (Exception $e) {
    error_log("Error: " . $e->getMessage());
    sendResponse(500, ['error' => 'Internal server error', 'message' => $e->getMessage()]);
}

function handleHealthCheck() {
    sendResponse(200, [
        'status' => 'healthy',
        'timestamp' => date('Y-m-d H:i:s'),
        'version' => '1.0.0'
    ]);
}

function handleDocumentUpload() {
    try {
        if (!isset($_FILES['document'])) {
            sendResponse(400, ['error' => 'No document provided']);
            return;
        }

        $file = $_FILES['document'];
        $documentController = new DocumentController();
        $result = $documentController->processDocument($file);
        
        sendResponse(200, $result);
    } catch (Exception $e) {
        error_log("Upload error: " . $e->getMessage());
        sendResponse(500, ['error' => 'Failed to process document', 'message' => $e->getMessage()]);
    }
}

function handleStatusCheck() {
    $status = [
        'service' => 'Document Processor API',
        'status' => 'running',
        'timestamp' => date('Y-m-d H:i:s'),
        'supported_formats' => ['.pdf', '.docx', '.xlsx', '.xlsm']
    ];
    sendResponse(200, $status);
}

function sendResponse($statusCode, $data) {
    http_response_code($statusCode);
    echo json_encode($data);
    exit();
}
?>