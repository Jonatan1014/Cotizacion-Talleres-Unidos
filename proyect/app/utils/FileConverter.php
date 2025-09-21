<?php
use PhpOffice\PhpWord\IOFactory as WordIOFactory;
use PhpOffice\PhpSpreadsheet\IOFactory as ExcelIOFactory;
use PhpOffice\PhpSpreadsheet\Writer\Pdf\Mpdf as PdfWriter;

class FileConverter {
    
    public function pdfToPng($pdfPath) {
        $outputPath = str_replace('.pdf', '.png', $pdfPath);
        $command = "pdftoppm -png -f 1 -l 1 '$pdfPath' > '$outputPath' 2>&1";
        exec($command, $output, $returnCode);
        
        if ($returnCode !== 0) {
            throw new Exception("Failed to convert PDF to PNG: " . implode("\n", $output));
        }
        
        return $outputPath;
    }
    
    public function docxToPdf($docxPath) {
        $outputPath = str_replace('.docx', '.pdf', $docxPath);
        
        // Usar LibreOffice para convertir
        $command = "libreoffice --headless --convert-to pdf --outdir '" . dirname($outputPath) . "' '$docxPath' 2>&1";
        exec($command, $output, $returnCode);
        
        if ($returnCode !== 0) {
            throw new Exception("Failed to convert DOCX to PDF: " . implode("\n", $output));
        }
        
        return $outputPath;
    }
    
    public function excelToPdf($excelPath) {
        $outputPath = str_replace(['.xlsx', '.xlsm'], '.pdf', $excelPath);
        
        // Usar LibreOffice para convertir
        $command = "libreoffice --headless --convert-to pdf --outdir '" . dirname($outputPath) . "' '$excelPath' 2>&1";
        exec($command, $output, $returnCode);
        
        if ($returnCode !== 0) {
            throw new Exception("Failed to convert Excel to PDF: " . implode("\n", $output));
        }
        
        return $outputPath;
    }
}
?>