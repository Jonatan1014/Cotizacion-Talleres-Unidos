"""
Tests for Smart Conversion endpoint
"""
import pytest
from pathlib import Path
from io import BytesIO
from fastapi.testclient import TestClient

from app.main import app
from app.services.smart_converter import FileTypeDetector, DetectedFileType


class TestFileTypeDetector:
    """Tests for FileTypeDetector."""
    
    def test_detect_word_docx(self):
        """Test detecting Word .docx files."""
        result = FileTypeDetector.detect("document.docx")
        assert result == DetectedFileType.WORD
    
    def test_detect_word_doc(self):
        """Test detecting Word .doc files."""
        result = FileTypeDetector.detect("document.doc")
        assert result == DetectedFileType.WORD
    
    def test_detect_excel_xlsx(self):
        """Test detecting Excel .xlsx files."""
        result = FileTypeDetector.detect("spreadsheet.xlsx")
        assert result == DetectedFileType.EXCEL
    
    def test_detect_excel_xls(self):
        """Test detecting Excel .xls files."""
        result = FileTypeDetector.detect("spreadsheet.xls")
        assert result == DetectedFileType.EXCEL
    
    def test_detect_pdf(self):
        """Test detecting PDF files."""
        result = FileTypeDetector.detect("document.pdf")
        assert result == DetectedFileType.PDF
    
    def test_detect_unknown(self):
        """Test detecting unknown file types."""
        result = FileTypeDetector.detect("file.xyz")
        assert result == DetectedFileType.UNKNOWN
    
    def test_detect_with_mime_type(self):
        """Test detection with MIME type."""
        result = FileTypeDetector.detect(
            "file.txt",
            "application/pdf"
        )
        assert result == DetectedFileType.PDF
    
    def test_detect_case_insensitive(self):
        """Test case insensitive detection."""
        result = FileTypeDetector.detect("DOCUMENT.DOCX")
        assert result == DetectedFileType.WORD


class TestSmartEndpoints:
    """Tests for Smart Conversion endpoints."""
    
    def test_get_supported_types(self, client):
        """Test getting supported types."""
        response = client.get("/api/v1/smart/supported-types")
        assert response.status_code == 200
        
        data = response.json()
        assert "supported_types" in data
        assert "output_formats" in data
        
        types = [t["type"] for t in data["supported_types"]]
        assert "word" in types
        assert "excel" in types
        assert "pdf" in types
    
    def test_detect_file_type_word(self, client):
        """Test file type detection for Word."""
        # Create a mock file
        file_content = b"Mock Word content"
        
        response = client.post(
            "/api/v1/smart/detect",
            files={"file": ("test.docx", file_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["detected_type"] == "word"
        assert data["supported"] is True
        assert data["conversion"]["target"] == "pdf"
    
    def test_detect_file_type_excel(self, client):
        """Test file type detection for Excel."""
        file_content = b"Mock Excel content"
        
        response = client.post(
            "/api/v1/smart/detect",
            files={"file": ("test.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["detected_type"] == "excel"
        assert data["supported"] is True
    
    def test_detect_file_type_pdf(self, client):
        """Test file type detection for PDF."""
        file_content = b"Mock PDF content"
        
        response = client.post(
            "/api/v1/smart/detect",
            files={"file": ("test.pdf", file_content, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["detected_type"] == "pdf"
        assert data["conversion"]["target"] == "jpg"
    
    def test_detect_file_type_unsupported(self, client):
        """Test file type detection for unsupported type."""
        file_content = b"Mock content"
        
        response = client.post(
            "/api/v1/smart/detect",
            files={"file": ("test.xyz", file_content, "application/octet-stream")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["detected_type"] == "unknown"
        assert data["supported"] is False
    
    def test_process_no_file(self, client):
        """Test processing without file."""
        response = client.post("/api/v1/smart/process")
        assert response.status_code == 422  # Validation error


class TestSmartConverterIntegration:
    """Integration tests for SmartConverter (require actual file processing)."""
    
    @pytest.fixture
    def sample_txt_file(self, tmp_path):
        """Create a sample text file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!")
        return file_path
    
    def test_process_unsupported_file(self, client):
        """Test processing unsupported file type."""
        file_content = b"Plain text content"
        
        response = client.post(
            "/api/v1/smart/process",
            files={"file": ("test.txt", file_content, "text/plain")}
        )
        
        # Should fail because .txt is not supported
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
