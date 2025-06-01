import pytest
from pathlib import Path
import cv2
import numpy as np
from app.core.ocr import process_receipt_image, preprocess_image, parse_receipt_text

@pytest.fixture
def sample_receipt_image():
    # Create a simple test image with some text
    img = np.zeros((300, 400), dtype=np.uint8)
    cv2.putText(img, "TESTOWY SKLEP", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    cv2.putText(img, "SUMA: 123,45", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    
    # Convert to bytes
    success, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

@pytest.mark.asyncio
async def test_process_receipt_image(sample_receipt_image):
    result = await process_receipt_image(sample_receipt_image)
    assert isinstance(result, dict)
    assert 'store_name' in result
    assert 'total_amount' in result
    assert 'items' in result

def test_preprocess_image():
    # Create a test image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    processed = preprocess_image(img)
    assert isinstance(processed, np.ndarray)
    assert len(processed.shape) == 2  # Should be grayscale

def test_parse_receipt_text():
    sample_text = """
    TESTOWY SKLEP
    ul. Testowa 1
    
    Mleko 3,50
    Chleb 4,20
    
    SUMA: 7,70
    """
    result = parse_receipt_text(sample_text)
    assert isinstance(result, dict)
    assert result['store_name'] == 'TESTOWY SKLEP'
    assert abs(result['total_amount'] - 7.70) < 0.01
    assert len(result['items']) == 2 