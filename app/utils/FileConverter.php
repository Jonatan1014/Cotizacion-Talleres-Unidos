<?php
class FileConverter {
    private $processedDir;

    public function __construct() {
        $this->processedDir = __DIR__ . '/../uploads/processed/';
        if (!is_dir($this->processedDir)) {
            mkdir($this->processedDir, 0777, true);
        }
    }

    public function convertPdfToPng($pdfPath) {
        try {
            // Verificar que el archivo exista y sea legible
            if (!file_exists($pdfPath) || !is_readable($pdfPath)) {
                throw new Exception('PDF file does not exist or is not readable: ' . $pdfPath);
            }

            // Contar el número de páginas en el PDF
            $command = "pdfinfo " . escapeshellarg($pdfPath) . " 2>&1";
            exec($command, $output, $returnCode);
            
            if ($returnCode !== 0) {
                throw new Exception('Failed to get PDF info. Command: ' . $command . ' Output: ' . implode("\n", $output));
            }
            
            $pages = 0;
            foreach ($output as $line) {
                if (preg_match('/^Pages:\s+(\d+)/', $line, $matches)) {
                    $pages = (int)$matches[1];
                    break;
                }
            }
            
            // Si el PDF tiene más de 1 página, devolver el archivo original sin cambios
            if ($pages > 1) {
                // Generar nuevo nombre con ID para mantener consistencia
                $originalNameWithoutExt = pathinfo($pdfPath, PATHINFO_FILENAME);
                $uniqueId = uniqid();
                $newFileName = $uniqueId . '-' . $originalNameWithoutExt . '.pdf';
                $outputPath = $this->processedDir . $newFileName;
                
                // Copiar el archivo original al directorio de procesados
                if (!copy($pdfPath, $outputPath)) {
                    throw new Exception('Failed to copy multi-page PDF to processed directory');
                }
                
                return $outputPath;
            }
            
            // Si el PDF tiene solo 1 página, convertir a PNG
            $originalNameWithoutExt = pathinfo($pdfPath, PATHINFO_FILENAME);
            $uniqueId = uniqid();
            $newFileName = $uniqueId . '-' . $originalNameWithoutExt . '.png';
            $outputPath = $this->processedDir . $newFileName;
            
            // Convert first page of PDF to PNG
            $command = "pdftoppm -png -f 1 -l 1 " . escapeshellarg($pdfPath) . " " . escapeshellarg($this->processedDir . $uniqueId . '-' . $originalNameWithoutExt) . " 2>&1";
            exec($command, $output, $returnCode);
            
            if ($returnCode !== 0) {
                throw new Exception('Failed to convert PDF to PNG. Command: ' . $command . ' Output: ' . implode("\n", $output));
            }
            
            // Verificar que el archivo se creó (pdftoppm puede crear con sufijo -1)
            $finalPath = $this->processedDir . $uniqueId . '-' . $originalNameWithoutExt . '-1.png';
            if (file_exists($finalPath)) {
                rename($finalPath, $outputPath);
            }
            
            if (!file_exists($outputPath)) {
                throw new Exception('PNG file was not created');
            }
            
            return $outputPath; // ← Devuelve la ruta absoluta
        } catch (Exception $e) {
            throw new Exception('PDF conversion failed: ' . $e->getMessage());
        }
    }

    public function convertDocxToPdf($docxPath) {
        try {
            // Verificar que el archivo exista y sea legible
            if (!file_exists($docxPath) || !is_readable($docxPath)) {
                throw new Exception('DOCX file does not exist or is not readable: ' . $docxPath);
            }

            // Obtener el nombre base del archivo original (sin extensión)
            $originalNameWithoutExt = pathinfo($docxPath, PATHINFO_FILENAME);
            
            // Generar ID único
            $uniqueId = uniqid();
            
            // Crear nuevo nombre: ID-OriginalName.pdf
            $newFileName = $uniqueId . '-' . $originalNameWithoutExt . '.pdf';
            $outputPath = $this->processedDir . $newFileName;
            
            // Copiar el archivo a un directorio temporal con permisos correctos
            $tempDir = '/tmp/libreoffice_' . uniqid();
            if (!is_dir($tempDir)) {
                mkdir($tempDir, 0777, true);
            }
            
            $tempFile = $tempDir . '/' . basename($docxPath);
            if (!copy($docxPath, $tempFile)) {
                $this->rrmdir($tempDir);
                throw new Exception('Failed to copy file to temporary directory');
            }
            
            // Asegurar permisos correctos
            chmod($tempFile, 0644);
            
            // Convert DOCX to PDF using LibreOffice with corrected command
            $command = "HOME=/tmp timeout 60 xvfb-run --auto-servernum --server-args='-screen 0 1024x768x24' libreoffice --headless --invisible --nodefault --nofirststartwizard --nolockcheck --nologo --norestore --convert-to pdf --outdir " . escapeshellarg($tempDir) . " " . escapeshellarg($tempFile) . " 2>&1";
            exec($command, $output, $returnCode);
            
            // Debug: mostrar salida de LibreOffice
            error_log("LibreOffice command: " . $command);
            error_log("LibreOffice output: " . implode("\n", $output));
            error_log("Return code: " . $returnCode);
            
            // Mover el archivo convertido al directorio final con el nuevo nombre
            $originalConvertedName = pathinfo($docxPath, PATHINFO_FILENAME) . '.pdf';
            $convertedFile = $tempDir . '/' . $originalConvertedName;
            
            if (file_exists($convertedFile)) {
                // Renombrar al nuevo nombre con ID
                rename($convertedFile, $outputPath);
                // Limpiar directorio temporal
                $this->rrmdir($tempDir);
            } else {
                // Limpiar directorio temporal
                $this->rrmdir($tempDir);
                throw new Exception('Failed to convert DOCX to PDF. LibreOffice could not create output file. Command: ' . $command . ' Output: ' . implode("\n", $output) . ' Return code: ' . $returnCode);
            }
            
            if (!file_exists($outputPath)) {
                throw new Exception('PDF file was not created');
            }
            
            return $outputPath; // ← Devuelve la ruta absoluta
        } catch (Exception $e) {
            throw new Exception('DOCX to PDF conversion failed: ' . $e->getMessage());
        }
    }

    public function convertExcelToPdf($excelPath) {
        try {
            // Verificar que el archivo exista y sea legible
            if (!file_exists($excelPath) || !is_readable($excelPath)) {
                throw new Exception('Excel file does not exist or is not readable: ' . $excelPath);
            }

            // Obtener el nombre base del archivo original (sin extensión)
            $originalNameWithoutExt = pathinfo($excelPath, PATHINFO_FILENAME);
            
            // Generar ID único
            $uniqueId = uniqid();
            
            // Crear nuevo nombre: ID-OriginalName.pdf
            $newFileName = $uniqueId . '-' . $originalNameWithoutExt . '.pdf';
            $outputPath = $this->processedDir . $newFileName;
            
            // Copiar el archivo a un directorio temporal con permisos correctos
            $tempDir = '/tmp/libreoffice_' . uniqid();
            if (!is_dir($tempDir)) {
                mkdir($tempDir, 0777, true);
            }
            
            $tempFile = $tempDir . '/' . basename($excelPath);
            if (!copy($excelPath, $tempFile)) {
                $this->rrmdir($tempDir);
                throw new Exception('Failed to copy file to temporary directory');
            }
            
            // Asegurar permisos correctos
            chmod($tempFile, 0644);
            
            // Convert Excel to PDF using LibreOffice
            $command = "HOME=/tmp timeout 60 xvfb-run --auto-servernum --server-args='-screen 0 1024x768x24' libreoffice --headless --invisible --nodefault --nofirststartwizard --nolockcheck --nologo --norestore --convert-to pdf --outdir " . escapeshellarg($tempDir) . " " . escapeshellarg($tempFile) . " 2>&1";
            exec($command, $output, $returnCode);
            
            // Mover el archivo convertido al directorio final con el nuevo nombre
            $originalConvertedName = pathinfo($excelPath, PATHINFO_FILENAME) . '.pdf';
            $convertedFile = $tempDir . '/' . $originalConvertedName;
            
            if (file_exists($convertedFile)) {
                // Renombrar al nuevo nombre con ID
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
            
            return $outputPath; // ← Devuelve la ruta absoluta
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