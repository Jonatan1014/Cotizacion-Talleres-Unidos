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
            $command = "pdftoppm -png -f 1 -l 1 '" . escapeshellarg($pdfPath) . "' '" . escapeshellarg($this->processedDir . $filename) . "' 2>&1";
            exec($command, $output, $returnCode);
            
            if ($returnCode !== 0) {
                throw new Exception('Failed to convert PDF to PNG. Command: ' . $command);
            }
            
            // Verificar que el archivo se creó
            $finalPath = $this->processedDir . $filename . '-1.png';
            if (file_exists($finalPath)) {
                rename($finalPath, $outputPath);
            }
            
            if (!file_exists($outputPath)) {
                throw new Exception('PNG file was not created');
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
            
            // Usar una ruta temporal para evitar problemas de permisos
            $tempDir = '/tmp/libreoffice_' . uniqid();
            mkdir($tempDir, 0755, true);
            
            // Convert DOCX to PDF using LibreOffice with better options
            $command = "HOME=/tmp timeout 60s libreoffice --headless --invisible --nodefault --nofirststartwizard --nolockcheck --nologo --norestore --convert-to pdf --outdir '" . escapeshellarg($tempDir) . "' '" . escapeshellarg($docxPath) . "' 2>&1";
            exec($command, $output, $returnCode);
            
            // Mover el archivo convertido al directorio final
            $convertedFile = $tempDir . '/' . $filename . '.pdf';
            
            if (file_exists($convertedFile)) {
                rename($convertedFile, $outputPath);
                // Limpiar directorio temporal
                $this->rrmdir($tempDir);
            } else {
                // Limpiar directorio temporal
                $this->rrmdir($tempDir);
                throw new Exception('Failed to convert DOCX to PDF. LibreOffice output: ' . implode("\n", $output) . ' Return code: ' . $returnCode);
            }
            
            if (!file_exists($outputPath)) {
                throw new Exception('PDF file was not created');
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
            
            // Usar una ruta temporal para evitar problemas de permisos
            $tempDir = '/tmp/libreoffice_' . uniqid();
            mkdir($tempDir, 0755, true);
            
            // Convert Excel to PDF using LibreOffice
            $command = "HOME=/tmp timeout 60s libreoffice --headless --invisible --nodefault --nofirststartwizard --nolockcheck --nologo --norestore --convert-to pdf --outdir '" . escapeshellarg($tempDir) . "' '" . escapeshellarg($excelPath) . "' 2>&1";
            exec($command, $output, $returnCode);
            
            // Mover el archivo convertido al directorio final
            $convertedFile = $tempDir . '/' . $filename . '.pdf';
            
            if (file_exists($convertedFile)) {
                rename($convertedFile, $outputPath);
                // Limpiar directorio temporal
                $this->rrmdir($tempDir);
            } else {
                // Limpiar directorio temporal
                $this->rrmdir($tempDir);
                throw new Exception('Failed to convert Excel to PDF. LibreOffice output: ' . implode("\n", $output) . ' Return code: ' . $returnCode);
            }
            
            if (!file_exists($outputPath)) {
                throw new Exception('PDF file was not created');
            }
            
            return $outputPath;
        } catch (Exception $e) {
            throw new Exception('Excel to PDF conversion failed: ' . $e->getMessage());
        }
    }

    // Función auxiliar para eliminar directorios recursivamente
    private function rrmdir($dir) {
        if (is_dir($dir)) {
            $objects = scandir($dir);
            foreach ($objects as $object) {
                if ($object != "." && $object != "..") {
                    if (is_dir($dir . "/" . $object))
                        $this->rrmdir($dir . "/" . $object);
                    else
                        unlink($dir . "/" . $object);
                }
            }
            rmdir($dir);
        }
    }
}
?>