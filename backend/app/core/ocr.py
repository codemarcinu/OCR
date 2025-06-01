import io
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Dict, Any
from datetime import datetime

async def process_receipt_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Process receipt image using OCR and extract relevant information.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Dictionary containing extracted receipt information
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Preprocess image
        img = preprocess_image(img)
        
        # Convert to PIL Image for Tesseract
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Extract text using Tesseract with Polish language
        text = pytesseract.image_to_string(pil_img, lang='pol')
        
        # Parse receipt text
        receipt_data = parse_receipt_text(text)
        
        return receipt_data
        
    except Exception as e:
        raise Exception(f"Failed to process image: {str(e)}")

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """
    Preprocess image for better OCR results.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to get black and white image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Remove noise
    denoised = cv2.fastNlMeansDenoising(binary)
    
    return denoised

def parse_receipt_text(text: str) -> Dict[str, Any]:
    """
    Parse receipt text to extract structured data.
    """
    lines = text.split('\n')
    receipt_data = {
        'store_name': '',
        'date': None,
        'total_amount': 0.0,
        'items': []
    }
    
    current_item = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try to find store name (usually in the first few lines)
        if not receipt_data['store_name'] and len(line) > 3:
            receipt_data['store_name'] = line
            continue
            
        # Look for date
        if not receipt_data['date']:
            date_match = extract_date(line)
            if date_match:
                receipt_data['date'] = date_match
                continue
                
        # Look for total amount
        if 'SUMA' in line.upper() or 'RAZEM' in line.upper():
            amount = extract_amount(line)
            if amount:
                receipt_data['total_amount'] = amount
                continue
                
        # Try to parse item
        item = parse_item_line(line)
        if item:
            receipt_data['items'].append(item)
            
    return receipt_data

def extract_date(line: str) -> str:
    """
    Extract date from text line.
    """
    # TODO: Implement more sophisticated date extraction
    # For now, return current date
    return datetime.now().date().isoformat()

def extract_amount(line: str) -> float:
    """
    Extract amount from text line.
    """
    try:
        # Remove all non-numeric characters except decimal point
        amount_str = ''.join(c for c in line if c.isdigit() or c in '.,')
        # Replace comma with dot for decimal point
        amount_str = amount_str.replace(',', '.')
        return float(amount_str)
    except:
        return 0.0

def parse_item_line(line: str) -> Dict[str, Any]:
    """
    Parse a line containing item information.
    """
    try:
        # Simple implementation - split by whitespace
        parts = line.split()
        if len(parts) >= 2:
            # Last part is usually the price
            price = extract_amount(parts[-1])
            # Rest is the name
            name = ' '.join(parts[:-1])
            return {
                'name': name,
                'quantity': 1,  # Default quantity
                'unit': 'szt',  # Default unit
                'price': price,
                'total_price': price
            }
    except:
        pass
    return None 