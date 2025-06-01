"""
Shared test fixtures and configuration.
"""
import pytest
import json
from pathlib import Path
from PIL import Image
import numpy as np

@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create and return a temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data")

@pytest.fixture
def sample_receipt_json():
    """Sample receipt data in JSON format."""
    return {
        "sklep": {
            "nazwa": "Lidl",
            "adres_sklepu": "ul. Testowa 123, 00-000 Warszawa",
            "nip": "123-45-67-890"
        },
        "data": "2024-01-01",
        "godzina": "12:34",
        "produkty": [
            {
                "nazwa": "MLEKO UHT 3.2% 1L",
                "ilosc": 1.0,
                "jednostka": "szt",
                "cena_jednostkowa_przed_rabatem": 3.99,
                "suma": 3.99,
                "stawka_vat": "A"
            },
            {
                "nazwa": "CHLEB WIEJSKI 500G",
                "ilosc": 1.0,
                "jednostka": "szt",
                "cena_jednostkowa_przed_rabatem": 4.50,
                "suma": 4.50,
                "stawka_vat": "B"
            }
        ],
        "platnosc": {
            "metoda": "karta",
            "suma": 8.49,
            "vat": [
                {
                    "stawka": "A",
                    "podstawa": 3.99,
                    "kwota": 0.92,
                    "procent": "23%"
                },
                {
                    "stawka": "B",
                    "podstawa": 4.50,
                    "kwota": 0.36,
                    "procent": "8%"
                }
            ]
        }
    }

@pytest.fixture
def sample_receipt_image(test_data_dir):
    """Create a sample receipt image for testing."""
    # Create a white background
    img = Image.new('RGB', (800, 1200), color='white')
    
    # Save in different formats
    paths = {}
    for fmt in ['jpg', 'png', 'bmp']:
        path = test_data_dir / f"sample_receipt.{fmt}"
        img.save(path)
        paths[fmt] = path
    
    return paths

@pytest.fixture
def sample_receipt_pdf(test_data_dir):
    """Create a sample receipt PDF for testing."""
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size
        
        # Add some text
        text = """
        LIDL
        ul. Testowa 123
        00-000 Warszawa
        NIP: 123-45-67-890
        
        MLEKO UHT 3.2% 1L      3.99 A
        CHLEB WIEJSKI 500G     4.50 B
        
        SUMA PLN               8.49
        """
        
        page.insert_text((72, 72), text)
        
        path = test_data_dir / "sample_receipt.pdf"
        doc.save(path)
        doc.close()
        
        return path
    except ImportError:
        pytest.skip("PyMuPDF not installed")

@pytest.fixture
def mock_ollama_response():
    """Mock response from Ollama API."""
    return {
        "model": "bielik",
        "created_at": "2024-01-01T12:34:56Z",
        "response": json.dumps({
            "standardized_name": "Mleko UHT",
            "category": "NABIAŁ",
            "is_frozen": False
        }),
        "done": True
    }

@pytest.fixture
def corrupt_image(test_data_dir):
    """Create a corrupt image file for testing error handling."""
    path = test_data_dir / "corrupt.jpg"
    with open(path, "wb") as f:
        f.write(b"Not an image file")
    return path

@pytest.fixture
def noisy_image(test_data_dir):
    """Create a noisy image for testing preprocessing."""
    # Create random noise
    noise = np.random.normal(0, 50, (800, 600))
    noise = np.clip(noise, 0, 255).astype(np.uint8)
    
    # Add some text-like structures
    noise[200:600, 100:500] = 255  # White rectangle
    
    # Convert to PIL Image
    img = Image.fromarray(noise, 'L')
    path = test_data_dir / "noisy_receipt.jpg"
    img.save(path)
    
    return path 