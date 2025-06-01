"""
Unit tests for OCR functionality.
"""
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
import fitz
from process_receipt import (
    extract_text_from_file,
    _preprocess_image,
    OCRError
)

@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample receipt image for testing."""
    img = Image.new('RGB', (800, 1200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add sample receipt text
    text = """
    LIDL
    ul. Przykładowa 123
    00-000 Warszawa
    NIP: 123-45-67-890
    
    MLEKO UHT 3.2% 1L      3.99
    CHLEB WIEJSKI 500G     4.50
    MASŁO EXTRA 200G       6.99
    """
    
    draw.text((50, 50), text, fill="black")
    path = tmp_path / "sample_receipt.jpg"
    img.save(path, quality=95)  # High quality JPEG
    return path

@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF with text for testing."""
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    
    text = """
    LIDL
    ul. Przykładowa 123
    00-000 Warszawa
    NIP: 123-45-67-890
    
    MLEKO UHT 3.2% 1L      3.99
    CHLEB WIEJSKI 500G     4.50
    MASŁO EXTRA 200G       6.99
    """
    
    page.insert_text((50, 50), text)
    doc.save(pdf_path)
    doc.close()
    return pdf_path

def test_extract_text_from_image(sample_image_path):
    """Test basic image text extraction."""
    result = extract_text_from_file(sample_image_path)
    assert "LIDL" in result
    assert "MLEKO" in result
    assert "3.99" in result

def test_extract_text_from_pdf(sample_pdf_path):
    """Test PDF text extraction."""
    result = extract_text_from_file(sample_pdf_path)
    assert "LIDL" in result
    assert "MLEKO" in result
    assert "3.99" in result

def test_image_preprocessing():
    """Test image preprocessing function."""
    # Create test image
    img = Image.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "Test Text", fill="black")
    
    # Test preprocessing
    processed = _preprocess_image(img)
    assert isinstance(processed, Image.Image)
    assert processed.size == (100, 100)

def test_error_handling_invalid_file():
    """Test error handling for invalid file."""
    with pytest.raises(Exception):
        extract_text_from_file(Path("nonexistent.jpg"))

def test_error_handling_corrupt_image(tmp_path):
    """Test error handling for corrupt image file."""
    # Create corrupt image file
    path = tmp_path / "corrupt.jpg"
    with open(path, 'wb') as f:
        f.write(b'Not an image file')
    
    with pytest.raises(Exception):
        extract_text_from_file(path)

def test_supported_image_formats(tmp_path):
    """Test support for different image formats."""
    formats = ['jpg', 'png', 'bmp', 'tiff']
    for fmt in formats:
        # Create image with text
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), "Test Text", fill="black")
        
        path = tmp_path / f"test.{fmt}"
        img.save(path)
        
        result = extract_text_from_file(path)
        assert "Test" in result 