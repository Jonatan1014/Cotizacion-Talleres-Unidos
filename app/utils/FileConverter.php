<?php
class FileConverter {
    private $processedDir;

    public function __construct() {
        $this->processedDir = __DIR__ . '/../uploads/processed/';
        if (!is_dir($this->processedDir)) {
            mkdir($this->processedDir, 0755, true);
        }
    }

    public function convertPdfToPng($pdfPath) {
        try {
            $filename = pathinfo($pdfPath, PATHINFO_FILENAME);
            $outputPath = $this->processedDir . $filename . '.png';
            
            // Convert first page of PDF to PNG
            $command = "pdftoppm -png -f 1 -l 1 '$pdfPath' > '$outputPath'";
            exec($command, $output, $returnCode);
            
            if ($returnCode !== 0) {
                throw new Exception('Failed to convert PDF to PNG');
            }
            
            return $outputPath;
        } catch (Exception $e) {
            throw new Exception('PDF to PNG conversion failed: ' . $e->getMessage());
        }
    }

    public function convertDocxToPdf($docxPath) {
        try {
            $filename = pathinfo($docxPath, PATHINFO_FILENAME);
            $outputPath = $this->processedDir . $filename . '.pdf';
            
            // Convert DOCX to PDF using LibreOffice
            $command = "libreoffice --headless --convert-to pdf --outdir '" . $this->processedDir . "' '$docxPath' 2>&1";
            exec($command, $output, $returnCode);
            
            if (!file_exists($outputPath)) {
                throw new Exception('Failed to convert DOCX to PDF');
            }
            
            return $outputPath;
        } catch (Exception $e) {
            throw new Exception('DOCX to PDF conversion failed: ' . $e->getMessage());
        }
    }

    public function convertExcelToPdf($excelPath) {
        try {
            $filename = pathinfo($excelPath, PATHINFO_FILENAME);
            $outputPath = $this->processedDir . $filename . '.pdf';
            
            // Convert Excel to PDF using LibreOffice
            $command = "libreoffice --headless --convert-to pdf --outdir '" . $this->processedDir . "' '$excelPath' 2>&1";
            exec($command, $output, $returnCode);
            
            if (!file_exists($outputPath)) {
                throw new Exception('Failed to convert Excel to PDF');
            }
            
            return $outputPath;
        } catch (Exception $e) {
            throw new Exception('Excel to PDF conversion failed: ' . $e->getMessage());
        }
    }
}
?>