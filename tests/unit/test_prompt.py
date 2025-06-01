"""
Unit tests for prompt processing.
"""
import pytest
import json
from pathlib import Path

def load_receipt_text(file_path: Path) -> str:
    """Load receipt text from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_prompt_template(file_path: Path) -> str:
    """Load prompt template from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def test_lidl_prompt_format():
    """Test if Lidl prompt template is valid."""
    prompt_path = Path('prompt_lidl.txt')
    prompt = load_prompt_template(prompt_path)
    
    # Check if prompt contains required sections
    assert "WAŻNE: Odpowiedz WYŁĄCZNIE w formacie JSON" in prompt
    assert "NIE GENERUJ kodu" in prompt
    assert "NIE DODAWAJ żadnych komentarzy ani wyjaśnień" in prompt
    
    # Check if JSON schema is defined
    assert '"sklep": {' in prompt
    assert '"produkty": [' in prompt
    assert '"platnosc": {' in prompt

def test_prompt_with_sample_receipt():
    """Test prompt with sample receipt data."""
    receipt_path = Path('tests/data/receipts/lidl_sample.txt')
    prompt_path = Path('prompt_lidl.txt')
    
    receipt_text = load_receipt_text(receipt_path)
    prompt = load_prompt_template(prompt_path)
    
    # Replace placeholder with actual receipt text
    full_prompt = prompt.replace('{{TEKST_PARAGONU}}', receipt_text)
    
    # Verify prompt structure
    assert receipt_text in full_prompt
    assert full_prompt.count(receipt_text) == 1
    
    # Check if prompt maintains JSON format specification
    assert full_prompt.startswith('WAŻNE: Odpowiedz WYŁĄCZNIE w formacie JSON')

def test_prompt_json_schema():
    """Test if prompt defines valid JSON schema."""
    prompt_path = Path('prompt_lidl.txt')
    prompt = load_prompt_template(prompt_path)
    
    # Extract JSON schema from prompt
    start = prompt.find('{')
    end = prompt.find('}', start) + 1
    schema_text = prompt[start:end]
    
    # Verify it's valid JSON
    try:
        schema = json.loads(schema_text)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON schema in prompt: {e}")
    
    # Check required fields
    assert "sklep" in schema
    assert "data" in schema
    assert "produkty" in schema
    assert "platnosc" in schema
    
    # Check product schema
    product_schema = schema["produkty"][0]
    assert "nazwa" in product_schema
    assert "ilosc" in product_schema
    assert "jednostka" in product_schema
    assert "suma" in product_schema
    
    # Check payment schema
    payment_schema = schema["platnosc"]
    assert "metoda" in payment_schema
    assert "suma" in payment_schema
    assert "vat" in payment_schema

def test_prompt_vat_rules():
    """Test if prompt defines correct VAT rules."""
    prompt_path = Path('prompt_lidl.txt')
    prompt = load_prompt_template(prompt_path)
    
    # Check VAT rate definitions
    assert "A: 23%" in prompt
    assert "B: 8%" in prompt
    assert "C: 5%" in prompt
    assert "D: 0%" in prompt

def test_prompt_processing_rules():
    """Test if prompt contains all processing rules."""
    prompt_path = Path('prompt_lidl.txt')
    prompt = load_prompt_template(prompt_path)
    
    rules = [
        "Format kwot: liczby z dwoma miejscami po przecinku",
        "Jeśli jakieś pole nie występuje w paragonie, pomiń je",
        "Zawsze podaj jednostkę miary",
        "cena_jednostkowa_przed_rabatem to cena przed rabatem na pozycję",
        "suma to końcowa kwota za całą pozycję"
    ]
    
    for rule in rules:
        assert rule in prompt, f"Missing rule: {rule}" 