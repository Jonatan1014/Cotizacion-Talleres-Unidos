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
                
                // NUEVO ENDPOINT: Transformar y devolver archivo multipart
                case '/api/documents/transform':
                    if ($method === 'POST') {
                        $this->transformAndReturnDocument();
                    } else {
                        $this->sendError(405, 'Method not allowed');
                    }
                    break;

                // NUEVO ENDPOINT: Transformar y devolver archivo binario
                case '/api/documents/transform/bin':
                    if ($method === 'POST') {
                        $this->transformAndReturnBinaryDocument();
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

                // NUEVO ENDPOINT: Recibir .zip o .rar (multipart), extraer y devolver binarios como multipart
                case '/api/uploads-ziprar':
                    if ($method === 'POST') {
                        $this->uploadArchiveAndProcess();
                    } else {
                        $this->sendError(405, 'Method not allowed');
                    }
                    break;

                // NUEVO ENDPOINT: Recibir .zip o .rar (binario), extraer y devolver binarios como multipart
                case '/api/uploads-ziprar/bin': // Añadir este caso
                    if ($method === 'POST') {
                         $this->uploadBinaryArchiveAndProcess();
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
                                'POST /api/documents/transform - Transform document and return (multipart)',
                                'POST /api/documents/transform/bin - Transform document and return (binary)',
                                'GET /api/health - Health check',
                                'POST /api/documents/manual - Manual processing (deprecated)',
                                'POST /api/uploads-ziprar - Upload and extract .zip/.rar, return binaries (multipart)',
                                'POST /api/uploads-ziprar/bin - Upload and extract .zip/.rar, return binaries (multipart)'
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
                'webhook_url' => $processResult['webhook_url'],
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
        $uploadResult = $this->documentService->uploadDocument($fileInfo, true);
        
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
                'webhook_url' => $processResult['webhook_url'],
                'message' => 'Document uploaded, processed and sent to webhook automatically'
            ]);
        } else {
            $this->sendError(400, 'Processing failed: ' . $processResult['message']);
        }
    }

    // NUEVO MÉTODO: Transformar y devolver archivo multipart
    private function transformAndReturnDocument() {
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

        // Procesar archivo (convertir)
        $processResult = $this->documentService->processDocumentForReturn($uploadResult['document']['file_path']);

        if ($processResult['success']) {
            // Devolver el archivo transformado
            $this->returnProcessedFile($processResult['processed_file']);
        } else {
            $this->sendError(400, 'Processing failed: ' . $processResult['message']);
        }
    }

    // NUEVO MÉTODO: Transformar y devolver archivo binario
    private function transformAndReturnBinaryDocument() {
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
        
        $uploadResult = $this->documentService->uploadDocument($fileInfo, true);
        
        if (!$uploadResult['success']) {
            $this->sendError(400, $uploadResult['message']);
            return;
        }
        
        // Procesar archivo (convertir)
        $processResult = $this->documentService->processDocumentForReturn($uploadResult['document']['file_path']);

        if ($processResult['success']) {
            // Devolver el archivo transformado en binario
            $this->returnProcessedFileBinary($processResult['processed_file']);
        } else {
            $this->sendError(400, 'Processing failed: ' . $processResult['message']);
        }
    }

    // Método para devolver archivo transformado
    private function returnProcessedFile($processedFilePath) {
        if (!file_exists($processedFilePath)) {
            $this->sendError(404, 'Processed file not found');
            return;
        }

        // Establecer headers para la descarga
        $mimeType = mime_content_type($processedFilePath);
        $fileName = basename($processedFilePath);
        
        header('Content-Type: ' . $mimeType);
        header('Content-Disposition: attachment; filename="' . $fileName . '"');
        header('Content-Length: ' . filesize($processedFilePath));
        header('Cache-Control: no-cache, must-revalidate');
        header('Expires: 0');
        
        // Enviar el archivo
        readfile($processedFilePath);
        exit;
    }

    // Método para devolver archivo transformado en binario
    private function returnProcessedFileBinary($processedFilePath) {
        if (!file_exists($processedFilePath)) {
            $this->sendError(404, 'Processed file not found');
            return;
        }

        // Establecer headers para devolver binario
        $mimeType = mime_content_type($processedFilePath);
        $fileName = basename($processedFilePath);
        
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . $fileName . '"');
        header('Content-Length: ' . filesize($processedFilePath));
        header('X-File-Name: ' . $fileName);
        header('X-File-Type: ' . $mimeType);
        
        // Enviar el archivo binario
        readfile($processedFilePath);
        exit;
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

    // NUEVO MÉTODO: Recibir archivo .zip o .rar como multipart, extraer y devolver binarios como multipart
    private function uploadArchiveAndProcess() {
        if (!isset($_FILES['archive'])) {
            $this->sendError(400, 'No archive provided');
            return;
        }
        $file = $_FILES['archive'];

        // Validar extensión
        $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        $allowed = ['zip', 'rar'];
        if (!in_array($ext, $allowed)) {
            $this->sendError(400, 'Archive type not allowed. Allowed: zip, rar');
            return;
        }

        // Limitar tamaño (por ejemplo 100MB)
        $maxBytes = 100 * 1024 * 1024; // 100 MB
        $fileSize = $file['size'];
        if ($fileSize > $maxBytes) {
            $this->sendError(400, 'Archive size exceeds ' . ($maxBytes / (1024*1024)) . 'MB limit');
            return;
        }

        // Guardar temporalmente en uploads
        $tmpName = uniqid() . '_' . basename($file['name']);
        $destPath = $this->uploadDir . $tmpName;
        if (!move_uploaded_file($file['tmp_name'], $destPath)) {
            $this->sendError(500, 'Failed to save uploaded archive');
            return;
        }

        // Delegar al servicio para extraer
        $result = $this->documentService->extractArchive($destPath); // <- Cambiado a extractArchive

        if ($result['success']) {
            // Devolver los archivos extraídos como multipart con contenido binario
            $this->sendExtractedFilesAsMultipart($result);
        } else {
            $this->sendError(400, $result['message']);
        }
    }

    // NUEVO MÉTODO: Recibir archivo .zip o .rar como binario, extraer y devolver binarios como multipart
    private function uploadBinaryArchiveAndProcess() {
        $input = file_get_contents('php://input');
        if (empty($input)) {
            $this->sendError(400, 'No archive data provided');
            return;
        }

        // Obtener nombre del archivo del header o usar uno por defecto
        $filename = $_SERVER['HTTP_X_FILENAME'] ?? ('archive_' . uniqid());

        // Asegurar que tenga extensión .zip o .rar
        $ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
        if (!in_array($ext, ['zip', 'rar'])) {
             // Intentar determinar el tipo de archivo por su contenido (opcional, más robusto)
             $finfo = new finfo(FILEINFO_MIME_TYPE);
             $mimeType = $finfo->buffer($input);
             $validMimeTypes = [
                 'application/zip' => 'zip',
                 'application/x-rar-compressed' => 'rar',
                 'application/vnd.rar' => 'rar' // Otro posible mime para rar
             ];
             if (isset($validMimeTypes[$mimeType])) {
                 $detectedExt = $validMimeTypes[$mimeType];
                 if ($ext === '' || !in_array($ext, ['zip', 'rar'])) {
                     // Asignar extensión detectada si no tenía o era inválida
                     $filename .= '.' . $detectedExt;
                     $ext = $detectedExt;
                 }
             }
             // Si después de intentar detectar, aún no es válida, error
             if (!in_array($ext, ['zip', 'rar'])) {
                 $this->sendError(400, 'Archive type not allowed or could not be determined. Allowed: zip, rar');
                 return;
             }
        }

        // Validar tamaño (100MB máximo)
        if (strlen($input) > 100 * 1024 * 1024) {
            $this->sendError(400, 'Archive size exceeds 100MB limit');
            return;
        }

        $filePath = $this->uploadDir . $filename;

        // Guardar el archivo binario
        if (file_put_contents($filePath, $input) === false) {
            $this->sendError(500, 'Failed to save archive');
            return;
        }

        // Delegar al servicio para extraer
        $result = $this->documentService->extractArchive($filePath); // <- Cambiado a extractArchive

        if ($result['success']) {
            // Devolver los archivos extraídos como multipart con contenido binario
            $this->sendExtractedFilesAsMultipart($result);
        } else {
            $this->sendError(400, $result['message']);
        }
    }

    // Método para enviar archivos extraídos como respuesta multipart con contenido binario
    private function sendExtractedFilesAsMultipart($extractionResult) {
        // Limpiar cualquier output buffer previo
        if (ob_get_level()) {
            ob_end_clean();
        }

        $boundary = '----WebKitFormBoundary' . uniqid(); // Generar un límite único

        // Enviar headers para multipart
        header('Content-Type: multipart/form-data; boundary=' . $boundary);
        header('Cache-Control: no-cache, must-revalidate');

        // Preparar metadatos como parte del multipart (opcional)
        $metadata = [
            'success' => $extractionResult['success'],
            'extracted_count' => $extractionResult['extracted_count'],
            'message' => $extractionResult['message'],
            'archive_path' => $extractionResult['archive_path'],
        ];

        foreach ($metadata as $key => $value) {
            echo "--{$boundary}\r\n";
            echo "Content-Disposition: form-data; name=\"{$key}\"\r\n";
            echo "Content-Type: text/plain\r\n\r\n";
            echo $value . "\r\n";
        }

        // Agregar cada archivo extraído como parte binaria
        foreach ($extractionResult['files'] as $index => $fileInfo) {
            $filePath = $fileInfo['path'];
            $fileName = $fileInfo['name'];
            $mimeType = $fileInfo['type'];

            if (file_exists($filePath)) {
                $fileContent = file_get_contents($filePath);

                echo "--{$boundary}\r\n";
                echo "Content-Disposition: form-data; name=\"file_{$index}\"; filename=\"{$fileName}\"\r\n";
                echo "Content-Type: {$mimeType}\r\n";
                echo "Content-Transfer-Encoding: binary\r\n\r\n";
                echo $fileContent . "\r\n"; // Enviar el contenido binario directamente
            }
        }

        // Finalizar el multipart
        echo "--{$boundary}--\r\n";

        // Salir para evitar que PHP agregue más contenido
        exit;
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