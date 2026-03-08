"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Test main health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data
    
    def test_readiness_check(self, client):
        """Test readiness endpoint."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True
    
    def test_liveness_check(self, client):
        """Test liveness endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["alive"] is True


class TestFormatsEndpoints:
    """Tests for formats endpoints."""
    
    def test_get_all_formats(self, client):
        """Test getting all supported formats."""
        response = client.get("/api/v1/formats")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure
        for format_info in data:
            assert "category" in format_info
            assert "input_formats" in format_info
            assert "output_formats" in format_info
    
    def test_get_image_formats(self, client):
        """Test getting image formats."""
        response = client.get("/api/v1/formats/image")
        assert response.status_code == 200
        
        data = response.json()
        assert data["category"] == "image"
        assert "jpg" in data["input_formats"]
        assert "png" in data["output_formats"]
    
    def test_get_invalid_category(self, client):
        """Test getting invalid category."""
        response = client.get("/api/v1/formats/invalid")
        assert response.status_code == 404


class TestConversionEndpoints:
    """Tests for conversion endpoints."""
    
    def test_validate_conversion_supported(self, client):
        """Test validating a supported conversion."""
        response = client.post(
            "/api/v1/conversion/validate",
            data={"source_format": "jpg", "target_format": "png"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["supported"] is True
    
    def test_validate_conversion_unsupported(self, client):
        """Test validating an unsupported conversion."""
        response = client.post(
            "/api/v1/conversion/validate",
            data={"source_format": "jpg", "target_format": "mp3"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["supported"] is False
    
    def test_convert_without_file(self, client):
        """Test conversion without file."""
        response = client.post(
            "/api/v1/conversion/convert",
            data={"target_format": "png"}
        )
        assert response.status_code == 422  # Validation error


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
