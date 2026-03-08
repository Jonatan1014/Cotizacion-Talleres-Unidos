"""
Test configuration and fixtures
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample image for testing."""
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='red')
    img_path = tmp_path / "test_image.jpg"
    img.save(img_path)
    
    return img_path


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("Hello, World! This is a test file.")
    
    return file_path
