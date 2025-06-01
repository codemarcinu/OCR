"""
Unit tests for LLM functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from product_analyzer import (
    analyze_receipt_products,
    _validate_product,
    _get_ai_product_analysis,
    ModelError
)

@pytest.fixture
def sample_receipt_text():
    """Sample receipt text for testing."""
    return """
    LIDL
    ul. Przykładowa 123
    00-000 Warszawa
    NIP: 123-45-67-890
    
    MLEKO UHT 3.2% 1L      3.99
    CHLEB WIEJSKI 500G     4.50
    MASŁO EXTRA 200G       6.99
    """

def test_product_validation():
    """Test product validation function."""
    valid_product = {
        "nazwa": "MLEKO UHT 3.2% 1L",
        "ilosc": 1.0,
        "suma": 3.99
    }
    
    result = _validate_product(valid_product)
    assert result["nazwa"] == "MLEKO UHT 3.2% 1L"
    assert result["ilosc"] == 1.0
    assert result["suma"] == 3.99

def test_product_validation_missing_fields():
    """Test validation of product with missing fields."""
    invalid_product = {
        "nazwa": "MLEKO UHT 3.2% 1L"
    }
    
    with pytest.raises(ValueError):
        _validate_product(invalid_product)

def test_product_analysis():
    """Test single product analysis."""
    product = {
        "nazwa": "MLEKO UHT 3.2% 1L",
        "ilosc": 1.0,
        "suma": 3.99
    }
    
    with patch("product_analyzer._get_ai_product_analysis") as mock_ai:
        mock_ai.return_value = {
            "standardized_name": "Mleko UHT",
            "category": "NABIAŁ",
            "is_frozen": False
        }
        
        result = _get_ai_product_analysis(product, "http://localhost:11434")
        assert result["standardized_name"] == "Mleko UHT"
        assert result["category"] == "NABIAŁ"
        assert not result["is_frozen"]

def test_frozen_product_detection():
    """Test detection of frozen products."""
    product = {
        "nazwa": "MROŻONA PIZZA 350G",
        "ilosc": 1.0,
        "suma": 8.99
    }
    
    with patch("product_analyzer._get_ai_product_analysis") as mock_ai:
        mock_ai.return_value = {
            "standardized_name": "Pizza mrożona",
            "category": "MROŻONKI",
            "is_frozen": True
        }
        
        result = _get_ai_product_analysis(product, "http://localhost:11434")
        assert result["is_frozen"]

def test_non_frozen_product_detection():
    """Test detection of non-frozen products."""
    product = {
        "nazwa": "CHLEB WIEJSKI 500G",
        "ilosc": 1.0,
        "suma": 4.50
    }
    
    with patch("product_analyzer._get_ai_product_analysis") as mock_ai:
        mock_ai.return_value = {
            "standardized_name": "Chleb pszenny",
            "category": "PIECZYWO",
            "is_frozen": False
        }
        
        result = _get_ai_product_analysis(product, "http://localhost:11434")
        assert not result["is_frozen"]

def test_llm_api_error_handling():
    """Test error handling for LLM API calls."""
    product = {
        "nazwa": "Test Product",
        "ilosc": 1.0,
        "suma": 9.99
    }
    
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("API Error")
        
        with pytest.raises(ModelError):
            _get_ai_product_analysis(product, "http://localhost:11434")

def test_receipt_products_analysis(sample_receipt_text):
    """Test analysis of multiple products from receipt."""
    products = [
        {
            "nazwa": "MLEKO UHT 3.2% 1L",
            "ilosc": 1.0,
            "suma": 3.99
        },
        {
            "nazwa": "CHLEB WIEJSKI 500G",
            "ilosc": 1.0,
            "suma": 4.50
        }
    ]
    
    with patch("product_analyzer._get_ai_product_analysis") as mock_ai:
        mock_ai.return_value = {
            "standardized_name": "Test",
            "category": "INNE",
            "is_frozen": False
        }
        
        results = analyze_receipt_products(products, sample_receipt_text, "http://localhost:11434")
        
        assert len(results) == 2
        for product in results:
            assert "standardized_name" in product
            assert "category" in product
            assert "is_frozen" in product 