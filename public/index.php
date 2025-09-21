<?php

$requestMethod = $_SERVER['REQUEST_METHOD'];
$requestUri = $_SERVER['REQUEST_URI'];

if ($requestMethod === 'POST' && $requestUri === '/convert') {
    $n8nUrl = getenv('N8N_WEBHOOK_URL');
    if (empty($n8nUrl)) {
        http_response_code(500);
        echo json_encode(['error' => 'N8N_WEBHOOK_URL environment variable not set']);
        exit;
    }

    if (!isset($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) {
        http_response_code(400);
        echo json_encode(['error' => 'No file uploaded or upload error']);
        exit;
    }

    $file = $_FILES['file'];
    $tempPath = $file['tmp_name'];
    $originalName = $file['name'];
    $extension = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));

    $allowedExtensions = ['pdf', 'docx', 'xlsx', 'xlsm'];
    if (!in_array($extension, $allowedExtensions)) {
        http_response_code(400);
        echo json_encode(['error' => 'Unsupported file type']);
        exit;
    }

    $convertedPath = null;
    switch ($extension) {
        case 'pdf':
            $convertedPath = processPDF($tempPath, $originalName);
            break;
        case 'docx':
            $convertedPath = processDOCX($tempPath, $originalName);
            break;
        case 'xlsx':
        case 'xlsm':
            $convertedPath = processExcel($tempPath, $originalName);
            break;
    }

    if (is_string($convertedPath) && file_exists($convertedPath)) {
        $webhookResponse = sendToWebhook($n8nUrl, $convertedPath, $originalName);
        unlink($tempPath);
        unlink($convertedPath);
        echo json_encode($webhookResponse);
        exit;
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Conversion failed']);
        exit;
    }
}

http_response_code(404);
echo json_encode(['error' => 'Not found']);

function processPDF($tempPath, $originalName) {
    $pages = exec("identify -format '%n' $tempPath 2>&1");
    $pages = trim($pages);
    if ($pages !== '1') {
        return "Error: PDF must have exactly one page (found $pages pages)";
    }

    $outputPath = sys_get_temp_dir() . '/' . pathinfo($originalName, PATHINFO_FILENAME) . '.png';
    $command = "convert -density 300 $tempPath -quality 90 $outputPath 2>&1";
    exec($command, $output, $returnVar);

    if ($returnVar !== 0) {
        return "Error converting PDF to PNG: " . implode("\n", $output);
    }

    return $outputPath;
}

function processDOCX($tempPath, $originalName) {
    $outputDir = sys_get_temp_dir();
    $baseName = pathinfo($originalName, PATHINFO_FILENAME);
    $command = "libreoffice --headless --convert-to pdf --outdir $outputDir $tempPath 2>&1";
    exec($command, $output, $returnVar);

    if ($returnVar !== 0) {
        return "Error converting DOCX to PDF: " . implode("\n", $output);
    }

    $generatedFile = glob("$outputDir/$baseName.pdf")[0];
    if (!$generatedFile) {
        return "Error: Generated PDF not found";
    }

    return $generatedFile;
}

function processExcel($tempPath, $originalName) {
    $outputDir = sys_get_temp_dir();
    $baseName = pathinfo($originalName, PATHINFO_FILENAME);
    $command = "libreoffice --headless --convert-to pdf --outdir $outputDir $tempPath 2>&1";
    exec($command, $output, $returnVar);

    if ($returnVar !== 0) {
        return "Error converting Excel to PDF: " . implode("\n", $output);
    }

    $generatedFile = glob("$outputDir/$baseName.pdf")[0];
    if (!$generatedFile) {
        return "Error: Generated PDF not found";
    }

    return $generatedFile;
}

function sendToWebhook($url, $convertedPath, $originalName) {
    $ch = curl_init($url);
    $cFile = new CURLFile($convertedPath, mime_content_type($convertedPath), basename($convertedPath));
    $postData = [
        'file' => $cFile,
        'original_name' => $originalName
    ];

    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode >= 200 && $httpCode < 300) {
        return ['success' => true, 'message' => 'File sent to webhook'];
    } else {
        return ['error' => 'Webhook failed', 'status' => $httpCode, 'response' => $response];
    }
}