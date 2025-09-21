<?php
require_once 'utils/FileConverter.php';

class DocumentService {
    private $converter;
    
    public function __construct() {
        $this->converter = new FileConverter();
    }
    
    public function processDocument($filePath, $extension) {
        switch ($extension) {
            case 'pdf':
                return $this->processPdf($filePath);
                
            case 'docx':
                return $this->processDocx($filePath);
                
            case 'xlsx':
            case 'xlsm':
                return $this->processExcel($filePath);
                
            default:
                throw new Exception("Unsupported file type: $extension");
        }
    }
    
    private function processPdf($filePath) {
        // Verificar si es PDF de una sola página
        $pages = $this->getPdfPageCount($filePath);
        
        if ($pages == 1) {
            // Convertir a PNG
            return $this->converter->pdfToPng($filePath);
        } else {
            // Devolver el PDF original si tiene más de una página
            return $filePath;
        }
    }
    
    private function processDocx($filePath) {
        // Convertir DOCX a PDF
        return $this->converter->docxToPdf($filePath);
    }
    
    private function processExcel($filePath) {
        // Extraer contenido y convertir a PDF
        return $this->converter->excelToPdf($filePath);
    }
    
    private function getPdfPageCount($filePath) {
        $command = "pdfinfo '$filePath' 2>/dev/null | grep Pages | awk '{print$2}'";
        $output = shell_exec($command);
        return intval(trim($output)) ?: 1;
    }
}
?>