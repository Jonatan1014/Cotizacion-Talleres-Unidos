# document_processor/app/services/document_processor.py
import os
import time
import subprocess
from pathlib import Path
from typing import Optional
import pandas as pd
from docx import Document
from pdf2image import convert_from_path
from PIL import Image
import io

from app.services.webhook_notifier import send_webhook_notification
from app.services.file_handler import create_output_directory
from app.api.models import WebhookPayload
from app.core.config import settings

def process_document(
    task_id: str,
    file_path: str,
    original_filename: str,
    webhook_url: str,
    metadata: Optional[dict] = None
):
    """
    Process document based on its type and conversion rules
    """
    start_time = time.time()
    output_filename = None
    error_message = None
    
    try:
        # Determine file extension
        file_ext = Path(original_filename).suffix.lower()
        
        # Create output directory
        output_dir = create_output_directory(task_id)
        
        # Process based on file type
        if file_ext == ".pdf":
            output_filename = convert_pdf_to_png(file_path, output_dir, original_filename)
        elif file_ext == ".docx":
            output_filename = convert_docx_to_pdf(file_path, output_dir, original_filename)
        elif file_ext in [".xlsx", ".xlsm"]:
            output_filename = convert_excel_to_pdf(file_path, output_dir, original_filename)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        processing_time = time.time() - start_time
        
        # Send success webhook
        payload = WebhookPayload(
            task_id=task_id,
            status="success",
            original_filename=original_filename,
            converted_filename=output_filename,
            download_url=f"/download/{task_id}/{output_filename}",
            processing_time=processing_time,
            metadata=metadata
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = str(e)
        
        # Send failure webhook
        payload = WebhookPayload(
            task_id=task_id,
            status="failed",
            original_filename=original_filename,
            error_message=error_message,
            processing_time=processing_time,
            metadata=metadata
        )
    
    # Send webhook notification
    send_webhook_notification(webhook_url, payload.dict())

def convert_pdf_to_png(pdf_path: str, output_dir: str, original_filename: str) -> str:
    """
    Convert PDF to PNG images
    """
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=200)
        
        # Save first page as PNG (in production, you might want all pages)
        output_filename = f"{Path(original_filename).stem}.png"
        output_path = Path(output_dir) / output_filename
        
        if images:
            images[0].save(output_path, 'PNG')
            return output_filename
        else:
            raise Exception("No pages found in PDF")
            
    except Exception as e:
        raise Exception(f"PDF to PNG conversion failed: {str(e)}")

def convert_docx_to_pdf(docx_path: str, output_dir: str, original_filename: str) -> str:
    """
    Convert DOCX to PDF using LibreOffice
    """
    try:
        output_filename = f"{Path(original_filename).stem}.pdf"
        output_path = Path(output_dir) / output_filename
        
        # Use LibreOffice to convert DOCX to PDF
        subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            docx_path
        ], check=True, capture_output=True)
        
        return output_filename
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"DOCX to PDF conversion failed: {e.stderr.decode()}")
    except Exception as e:
        raise Exception(f"DOCX to PDF conversion failed: {str(e)}")

def convert_excel_to_pdf(excel_path: str, output_dir: str, original_filename: str) -> str:
    """
    Convert Excel files to PDF with content extraction
    """
    try:
        # First, extract content to CSV for additional processing if needed
        csv_filename = f"{Path(original_filename).stem}.csv"
        csv_path = Path(output_dir) / csv_filename
        
        # Read Excel file
        if Path(excel_path).suffix.lower() == '.xlsm':
            df = pd.read_excel(excel_path, engine='openpyxl')
        else:
            df = pd.read_excel(excel_path)
        
        # Save as CSV
        df.to_csv(csv_path, index=False)
        
        # Convert to PDF using LibreOffice
        output_filename = f"{Path(original_filename).stem}.pdf"
        output_path = Path(output_dir) / output_filename
        
        subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            excel_path
        ], check=True, capture_output=True)
        
        return output_filename
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Excel to PDF conversion failed: {e.stderr.decode()}")
    except Exception as e:
        raise Exception(f"Excel to PDF conversion failed: {str(e)}")