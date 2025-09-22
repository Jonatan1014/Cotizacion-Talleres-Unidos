<?php
require_once 'services/DocumentService.php';
require_once 'models/Document.php';

class DocumentController {
    private $documentService;
    private $uploadDir;

    public function __construct() {
        $this->documentService = new DocumentService();
        $this->uploadDir = __DIR__ . '/../uploads/';
    }

    public function handleRequest() {
        $method = $_SERVER['REQUEST_METHOD'];
        $uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
        $path = str_replace('/index.php', '', $uri);

        try {
            switch ($path) {
                case '/api/documents':
                    if ($method === 'POST') {
                        $this->uploadAndProcessDocument();
                    } elseif ($method === 'GET') {
                        $this->getDocuments();
                    } else {
                        $this->sendError(405, 'Method not allowed');
                    }
                    break;
                
                case '/api/documents/bin':
                    if ($method === 'POST') {
                        $this->uploadBinaryDocument();
                    } else {
                        $this->sendError(405, 'Method not allowed');
                    }
                    break;

                case '/api/documents/manual':
                    if ($method === 'POST') {
                        $this->processDocument();
                    } else {
                        $this->sendError(405, 'Method not allowed');
                    }
                    break;
                
                case '/api/health':
                    if ($method === 'GET') {
                        $this->healthCheck();
                    } else {
                        $this->sendError(405, 'Method not allowed');
                    }
                    break;
                
                case '/':
                    if ($method === 'GET') {
                        $this->sendResponse(200, [
                            'message' => 'Document Processing API - Automatic Conversion',
                            'endpoints' => [
                                'POST /api/documents - Upload and auto-process document (multipart)',
                                'POST /api/documents/bin - Upload and auto-process document (binary)',
                                'GET /api/health - Health check',
                                'POST /api/documents/manual - Manual processing (deprecated)'
                            ]
                        ]);
                    } else {
                        $this->sendError(405, 'Method not allowed');
                    }
                    break;
                
                default:
                    $this->sendError(404, 'Endpoint not found');
            }
        } catch (Exception $e) {
            $this->sendError(500, 'Internal server error: ' . $e->getMessage());
        }
    }

    private function uploadAndProcessDocument() {
        if (!isset($_FILES['document'])) {
            $this->sendError(400, 'No document provided');
            return;
        }

        $file = $_FILES['document'];
        $uploadResult = $this->documentService->uploadDocument($file);

        if (!$uploadResult['success']) {
            $this->sendError(400, $uploadResult['message']);
            return;
        }

        // Procesar automáticamente
        $processResult = $this->documentService->processDocument($uploadResult['document']['file_path']);

        if ($processResult['success']) {
            $this->sendResponse(200, [
                'success' => true,
                'upload' => $uploadResult['document'],
                'processing' => [
                    'processed_file' => $processResult['processed_file'],
                    'webhook_sent' => $processResult['webhook_sent']
                ],
                'message' => 'Document uploaded, processed and sent to webhook automatically'
            ]);
        } else {
            $this->sendError(400, 'Processing failed: ' . $processResult['message']);
        }
    }

    private function uploadBinaryDocument() {
        $input = file_get_contents('php://input');
        
        if (empty($input)) {
            $this->sendError(400, 'No document data provided');
            return;
        }
        
        // Obtener nombre del archivo del header o usar uno por defecto
        $filename = $_SERVER['HTTP_X_FILENAME'] ?? ('document_' . uniqid());
        
        // Asegurar que tenga extensión
        if (pathinfo($filename, PATHINFO_EXTENSION) === '') {
            // Intentar determinar el tipo de archivo por su contenido
            $finfo = new finfo(FILEINFO_MIME_TYPE);
            $mimeType = $finfo->buffer($input);
            
            $extensions = [
                'application/pdf' => '.pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document' => '.docx',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' => '.xlsx',
                'application/vnd.ms-excel.sheet.macroEnabled.12' => '.xlsm'
            ];
            
            $extension = $extensions[$mimeType] ?? '.bin';
            $filename .= $extension;
        }
        
        $filePath = $this->uploadDir . $filename;
        
        // Validar tamaño (50MB máximo)
        if (strlen($input) > 50 * 1024 * 1024) {
            $this->sendError(400, 'File size exceeds 50MB limit');
            return;
        }
        
        // Validar tipo de archivo
        $allowedExtensions = ['pdf', 'docx', 'xlsx', 'xlsm'];
        $fileExtension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
        if (!in_array($fileExtension, $allowedExtensions)) {
            $this->sendError(400, 'File type not allowed. Allowed types: ' . implode(', ', $allowedExtensions));
            return;
        }
        
        // Guardar el archivo binario
        if (file_put_contents($filePath, $input) === false) {
            $this->sendError(500, 'Failed to save document');
            return;
        }
        
        // Crear un array similar al $_FILES para mantener consistencia
        $fileInfo = [
            'name' => $filename,
            'type' => mime_content_type($filePath),
            'tmp_name' => $filePath,
            'error' => 0,
            'size' => strlen($input)
        ];
        
        // Usar el mismo método de procesamiento que uploadAndProcessDocument
        $uploadResult = $this->documentService->uploadDocument($fileInfo, true); // true = ya está guardado
        
        if (!$uploadResult['success']) {
            $this->sendError(400, $uploadResult['message']);
            return;
        }
        
        // Procesar automáticamente
        $processResult = $this->documentService->processDocument($uploadResult['document']['file_path']);
        
        if ($processResult['success']) {
            $this->sendResponse(200, [
                'success' => true,
                'upload' => $uploadResult['document'],
                'processing' => [
                    'processed_file' => $processResult['processed_file'],
                    'webhook_sent' => $processResult['webhook_sent']
                ],
                'message' => 'Document uploaded, processed and sent to webhook automatically'
            ]);
        } else {
            $this->sendError(400, 'Processing failed: ' . $processResult['message']);
        }
    }

    private function processDocument() {
        $input = json_decode(file_get_contents('php://input'), true);
        
        if (!$input || !isset($input['document_id'])) {
            $this->sendError(400, 'Document ID is required');
            return;
        }

        $result = $this->documentService->processDocument($input['document_id']);

        if ($result['success']) {
            $this->sendResponse(200, $result);
        } else {
            $this->sendError(400, $result['message']);
        }
    }

    private function getDocuments() {
        $documents = $this->documentService->getAllDocuments();
        $this->sendResponse(200, ['documents' => $documents]);
    }

    private function healthCheck() {
        $this->sendResponse(200, [
            'status' => 'healthy',
            'timestamp' => date('Y-m-d H:i:s'),
            'version' => '1.0.0'
        ]);
    }

    private function sendResponse($statusCode, $data) {
        http_response_code($statusCode);
        echo json_encode($data);
    }

    private function sendError($statusCode, $message) {
        http_response_code($statusCode);
        echo json_encode([
            'success' => false,
            'message' => $message
        ]);
    }
}
?>