#!/usr/bin/env python3
"""
Moduł przetwarzania paragonów z OCR i LLM.

Ten moduł zawiera funkcje do:
1. Ekstrakcji tekstu z plików PDF i obrazów przy użyciu OCR
2. Komunikacji z modelem Ollama do analizy tekstu
3. Wykrywania sklepu na podstawie tekstu paragonu
4. Przetwarzania i walidacji danych paragonu
"""

import argparse
import json
import requests
import sys
import re
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import fitz
from product_analyzer import analyze_receipt_products
import time
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageEnhance

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Biblioteki Pytesseract lub Pillow nie są zainstalowane. OCR dla obrazów nie będzie działać.")
    print("Zainstaluj je używając: pip install pytesseract pillow")
    pytesseract = None
    Image = None

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Biblioteka PyMuPDF (fitz) nie jest zainstalowana. OCR dla PDF nie będzie działać.")
    print("Zainstaluj ją używając: pip install PyMuPDF")
    fitz = None

# Domyślne ustawienia
DEFAULT_OLLAMA_MODEL = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_SYSTEM_PROMPT_FILE = "prompt_dla_bielik.txt"

# Wzorce dla rozpoznawania sklepów
STORE_PATTERNS = {
    'lidl': {
        'patterns': [
            r'Lidl Sp\. z o\.o\. sp\.k\.',
            r'Lidl Polska',
            r'Lidl Plus',
        ],
        'prompt_file': 'prompt_lidl.txt',
        'weight': 1.0
    },
    'biedronka': {
        'patterns': [
            r'Jeronimo Martins',
            r'Biedronka',
            r'JMP S\.A\.',
        ],
        'prompt_file': 'prompt_biedronka.txt',
        'weight': 1.0
    },
    'kaufland': {
        'patterns': [
            r'Kaufland Polska',
            r'Kaufland',
        ],
        'prompt_file': 'prompt_kaufland.txt',
        'weight': 1.0
    },
    'auchan': {
        'patterns': [
            r'Auchan Polska',
            r'Auchan',
        ],
        'prompt_file': 'prompt_auchan.txt',
        'weight': 1.0
    }
}

def _preprocess_image(image):
    """
    Preprocessuje obraz dla lepszych wyników OCR.
    
    Args:
        image: PIL Image object
        
    Returns:
        Preprocessed PIL Image object
    """
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance
    
    # Konwertuj do OpenCV
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Przeskaluj obraz do większego rozmiaru
    scale_factor = 3.0  # Zwiększamy skalę dla lepszej rozdzielczości
    width = int(img.shape[1] * scale_factor)
    height = int(img.shape[0] * scale_factor)
    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)
    
    # Konwertuj do skali szarości
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Zwiększ kontrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Usuń szum
    denoised = cv2.fastNlMeansDenoising(gray, h=10)  # Zmniejszamy parametr h dla zachowania detali
    
    # Binaryzacja adaptacyjna
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15,  # Mniejszy rozmiar bloku dla lepszego rozpoznawania małego tekstu
        8    # Mniejsza stała C dla lepszego kontrastu
    )
    
    # Morfologia - usuwanie małych artefaktów
    kernel = np.ones((1,1), np.uint8)  # Mniejszy kernel dla zachowania małego tekstu
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Deskew jeśli potrzebne
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) > 0:  # Sprawdź czy są jakieś białe piksele
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        center = tuple(np.array(binary.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        binary = cv2.warpAffine(
            binary,
            rot_mat,
            binary.shape[1::-1],
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
    
    # Konwertuj z powrotem do PIL
    processed = Image.fromarray(binary)
    
    # Zwiększ ostrość
    enhancer = ImageEnhance.Sharpness(processed)
    processed = enhancer.enhance(1.5)  # Zmniejszamy wzmocnienie ostrości
    
    # Zwiększ kontrast
    enhancer = ImageEnhance.Contrast(processed)
    processed = enhancer.enhance(1.5)  # Zmniejszamy wzmocnienie kontrastu
    
    return processed

def extract_text_from_file(file_path: Path) -> str:
    """
    Ekstrahuje tekst z pliku (PDF lub obraz).
    
    Args:
        file_path: Ścieżka do pliku
        
    Returns:
        Wyekstrahowany tekst
    """
    try:
        if file_path.suffix.lower() == '.pdf':
            text = _extract_text_from_pdf(file_path)
        else:
            text = _extract_text_from_image(file_path)
            
        if text.strip():
            logger.info(f"Pomyślnie wykonano OCR na obrazie: {file_path}")
            logger.debug("Wyekstrahowany tekst:")
            logger.debug("-" * 80)
            logger.debug(text)
            logger.debug("-" * 80)
            logger.debug(f"Długość tekstu: {len(text)} znaków")
            
            # Log OCR output to file for debugging
            debug_file = file_path.parent / f"{file_path.stem}_ocr.txt"
            debug_file.write_text(text, encoding='utf-8')
            logger.debug(f"Zapisano tekst OCR do: {debug_file}")
            
            return text
        else:
            raise Exception("Wyekstrahowany tekst jest pusty")
            
    except Exception as e:
        logger.error(f"Błąd podczas ekstrakcji tekstu z pliku {file_path}: {str(e)}")
        raise

def _extract_text_from_pdf(file_path: Path) -> str:
    """
    Ekstrahuje tekst z pliku PDF, próbując różne metody.
    """
    text = ""
    
    try:
        # 1. Próba bezpośredniego wydobycia tekstu z PDF
        pdf_doc = fitz.open(file_path)
        for page in pdf_doc:
            text += page.get_text()
        pdf_doc.close()
        
        if text.strip():
            logger.info(f"Pomyślnie wyekstrahowano tekst z PDF: {file_path}")
            return text
            
        # 2. Jeśli nie ma tekstu, konwertujemy na obrazy i używamy OCR
        logger.info(f"PDF {file_path} nie zawiera warstwy tekstowej, używam OCR...")
        
        # Konwertuj PDF na obrazy z wyższą rozdzielczością
        images = convert_from_path(
            file_path,
            dpi=300,  # Wyższa rozdzielczość dla lepszej jakości OCR
            grayscale=True  # Konwersja do skali szarości dla lepszego OCR
        )
        
        # Użyj OCR na każdej stronie
        text = ""
        for i, image in enumerate(images, 1):
            # Popraw kontrast obrazu
            image = image.convert('L')  # Konwersja do skali szarości
            image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binaryzacja
            
            # Wykonaj OCR z dodatkowymi parametrami
            page_text = pytesseract.image_to_string(
                image,
                lang='pol',
                config='--psm 6'  # Tryb segmentacji strony: zakładamy jednolity blok tekstu
            )
            
            text += page_text + "\n"
            logger.info(f"Wykonano OCR na stronie {i} z PDF: {file_path}")
        
        if not text.strip():
            raise Exception("Nie udało się wyekstrahować tekstu żadną metodą")
            
        return text
        
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania PDF {file_path}: {str(e)}")
        raise

def _extract_text_from_image(file_path: Path) -> str:
    """
    Ekstrahuje tekst z pliku obrazu.
    
    Args:
        file_path: Ścieżka do pliku obrazu
        
    Returns:
        Wyekstrahowany tekst
    """
    try:
        # Wczytaj obraz
        image = Image.open(file_path)
        
        # Preprocessuj obraz
        processed_image = _preprocess_image(image)
        
        # Wykonaj OCR z dodatkowymi parametrami
        text = pytesseract.image_to_string(
            processed_image,
            lang='pol',
            config='--psm 6 --oem 3'  # Tryb segmentacji strony i silnik OCR
        )
        
        if not text.strip():
            # Spróbuj ponownie z oryginalnym obrazem
            logger.warning("OCR nie zwrócił tekstu dla przetworzonego obrazu, próbuję z oryginałem")
            text = pytesseract.image_to_string(
                image,
                lang='pol',
                config='--psm 6 --oem 3'
            )
            
        if not text.strip():
            raise OCRError("OCR nie zwrócił żadnego tekstu")
            
        logger.info(f"Pomyślnie wykonano OCR na obrazie: {file_path}")
        return text
        
    except Exception as e:
        logger.error(f"Błąd podczas OCR obrazu {file_path}: {str(e)}")
        raise

def load_system_prompt(prompt_file: Path) -> str:
    """
    Wczytuje prompt systemowy z pliku.
    
    Args:
        prompt_file: Ścieżka do pliku z promptem
        
    Returns:
        Tekst promptu
    """
    try:
        if not prompt_file.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku promptu: {prompt_file}")
            
        prompt = prompt_file.read_text(encoding='utf-8')
        logger.info(f"Wczytano prompt systemowy z: {prompt_file}")
        return prompt
        
    except Exception as e:
        logger.error(f"Błąd podczas wczytywania promptu z {prompt_file}: {str(e)}")
        raise

def _validate_and_repair_json(response_text: str) -> str:
    """
    Waliduje i naprawia odpowiedź JSON od modelu.
    
    Args:
        response_text: Tekst odpowiedzi do przetworzenia
        
    Returns:
        Naprawiony tekst JSON
        
    Raises:
        json.JSONDecodeError: Jeśli nie udało się naprawić JSON
    """
    # 1. Usuń potencjalne znaczniki kodu
    text = response_text.replace('```json', '').replace('```', '').strip()
    
    # 2. Znajdź początek i koniec JSON
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx == -1 or end_idx == -1:
        raise json.JSONDecodeError(
            "Nie znaleziono poprawnej struktury JSON",
            response_text,
            0
        )
    
    # 3. Wytnij tylko część JSON
    text = text[start_idx:end_idx + 1]
    
    # 4. Usuń znaki nowej linii i dodatkowe spacje
    text = re.sub(r'\s+', ' ', text)
    
    # 5. Usuń spacje po lewej stronie dwukropka
    text = re.sub(r'\s+:', ':', text)
    
    # 6. Usuń spacje po prawej stronie dwukropka
    text = re.sub(r':\s+', ':', text)
    
    # 7. Usuń spacje po lewej stronie przecinka
    text = re.sub(r'\s+,', ',', text)
    
    # 8. Usuń spacje po prawej stronie przecinka
    text = re.sub(r',\s+', ',', text)
    
    # 9. Usuń spacje po lewej stronie nawiasów
    text = re.sub(r'\s+\{', '{', text)
    text = re.sub(r'\s+\[', '[', text)
    text = re.sub(r'\s+\}', '}', text)
    text = re.sub(r'\s+\]', ']', text)
    
    # 10. Usuń spacje po prawej stronie nawiasów
    text = re.sub(r'\{\s+', '{', text)
    text = re.sub(r'\[\s+', '[', text)
    text = re.sub(r'\}\s+', '}', text)
    text = re.sub(r'\]\s+', ']', text)
    
    # 11. Usuń potencjalne znaki ucieczki
    text = text.replace('\\"', '"')
    
    # 12. Spróbuj naprawić typowe problemy
    try:
        # Próba parsowania
        parsed = json.loads(text)
        
        # Sprawdź wymagane pola
        required_fields = ['data', 'sklep', 'produkty', 'platnosc']
        missing_fields = [field for field in required_fields if field not in parsed]
        
        if missing_fields:
            raise json.JSONDecodeError(
                f"Brak wymaganych pól: {', '.join(missing_fields)}", 
                text, 
                0
            )
            
        # Sprawdź i napraw pola numeryczne
        if 'produkty' in parsed:
            for produkt in parsed['produkty']:
                for field in ['ilosc', 'cena_jednostkowa_przed_rabatem', 'suma']:
                    if field in produkt and isinstance(produkt[field], str):
                        try:
                            produkt[field] = float(produkt[field].replace(',', '.'))
                        except (ValueError, TypeError):
                            logger.warning(f"Nie udało się przekonwertować pola {field} na liczbę")
                            
        # Sprawdź i napraw daty
        if 'data' in parsed and not re.match(r'^\d{4}-\d{2}-\d{2}$', parsed['data']):
            try:
                # Próba parsowania różnych formatów daty
                for fmt in ['%d.%m.%Y', '%Y.%m.%d', '%d-%m-%Y']:
                    try:
                        date_obj = datetime.strptime(parsed['data'], fmt)
                        parsed['data'] = date_obj.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
            except Exception:
                logger.warning("Nie udało się przekonwertować daty do formatu YYYY-MM-DD")
        
        # Konwertuj z powrotem do tekstu
        return json.dumps(parsed)
        
    except json.JSONDecodeError as e:
        logger.error(f"Nie udało się naprawić JSON: {str(e)}")
        raise

def query_ollama(url: str, model: str, prompt: str) -> str:
    """
    Wysyła zapytanie do serwera Ollama.
    
    Args:
        url: URL serwera Ollama
        model: Nazwa modelu do użycia
        prompt: Tekst promptu
        
    Returns:
        Odpowiedź od modelu
    """
    logger.info(f"Wysyłanie zapytania do Ollama (model: {model})...")
    
    # Maksymalna liczba prób
    max_retries = 3
    retry_delay = 2  # sekundy
    
    for attempt in range(max_retries):
        try:
            # Wyślij zapytanie
            response = requests.post(url, json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 1024,
                "stop": ["\n\n", "```"]
            }, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(f"Błąd od serwera Ollama: {result['error']}")
                
            if 'response' not in result:
                raise Exception("Brak odpowiedzi w zwróconych danych")
                
            logger.info("Otrzymano odpowiedź od Ollama.")
            
            # Walidacja i naprawa JSON
            try:
                response_text = _validate_and_repair_json(result['response'])
                return response_text
                
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Próba {attempt + 1}/{max_retries}: Niepoprawna odpowiedź JSON, próbuję ponownie...")
                    logger.warning(f"Szczegóły błędu: {str(e)}")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("\nOtrzymano niepoprawną odpowiedź JSON od modelu:")
                    logger.error("-" * 80)
                    logger.error(result['response'])
                    logger.error("-" * 80)
                    logger.error(f"Szczegóły błędu: {str(e)}")
                    raise Exception("Nie udało się naprawić odpowiedzi JSON po 3 próbach")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"Próba {attempt + 1}/{max_retries}: Błąd połączenia, próbuję ponownie...")
                time.sleep(retry_delay)
                continue
            else:
                error_msg = f"Błąd połączenia z serwerem Ollama ({url}): {str(e)}\n"
                error_msg += "Upewnij się, że serwer Ollama jest uruchomiony i dostępny."
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Próba {attempt + 1}/{max_retries}: Nieoczekiwany błąd, próbuję ponownie...")
                logger.warning(f"Szczegóły błędu: {str(e)}")
                time.sleep(retry_delay)
                continue
            else:
                logger.error(f"Nieoczekiwany błąd po 3 próbach: {str(e)}")
                raise

def detect_store(text: str) -> Tuple[Optional[str], float]:
    """
    Wykrywa sklep na podstawie tekstu paragonu.
    
    Args:
        text: Tekst paragonu
        
    Returns:
        Tuple[Optional[str], float]: (identyfikator sklepu, pewność)
    """
    best_match = None
    best_score = 0.0
    
    for store_id, store_info in STORE_PATTERNS.items():
        score = 0.0
        for pattern in store_info['patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches) * store_info['weight']
        
        if score > best_score:
            best_score = score
            best_match = store_id
    
    if best_match:
        logger.info(f"Wykryto paragon ze sklepu: {best_match} (pewność: {best_score})")
    else:
        logger.warning("UWAGA: Nie rozpoznano sklepu z paragonu.")
        
    return best_match, best_score

def get_store_prompt(store_id: Optional[str], default_prompt_file: Path) -> Tuple[str, Path]:
    """
    Zwraca odpowiedni prompt dla wykrytego sklepu.
    
    Args:
        store_id: Identyfikator sklepu
        default_prompt_file: Domyślny plik promptu
        
    Returns:
        Tuple[str, Path]: (tekst promptu, ścieżka do pliku promptu)
    """
    if store_id and store_id in STORE_PATTERNS:
        store_prompt_file = Path(STORE_PATTERNS[store_id]['prompt_file'])
        if store_prompt_file.exists():
            logger.info(f"Używam promptu dla sklepu {store_id}: {store_prompt_file}")
            return load_system_prompt(store_prompt_file), store_prompt_file
    
    logger.info(f"Używam domyślnego promptu: {default_prompt_file}")
    return load_system_prompt(default_prompt_file), default_prompt_file

def _validate_and_repair_vat(vat_data: List[Dict]) -> List[Dict]:
    """
    Waliduje i naprawia dane VAT.
    
    Args:
        vat_data: Lista słowników z danymi VAT
        
    Returns:
        Naprawiona lista danych VAT
    """
    try:
        if not isinstance(vat_data, list):
            logger.warning("Dane VAT nie są listą, zwracam pustą listę")
            return []
        
        valid_vat = []
        
        for vat_entry in vat_data:
            try:
                # 1. Sprawdź czy to słownik
                if not isinstance(vat_entry, dict):
                    logger.warning(f"Pominięto niepoprawny wpis VAT: {vat_entry}")
                    continue
                
                # 2. Sprawdź wymagane pola
                required_fields = ['stawka', 'podstawa', 'kwota']
                missing_fields = [field for field in required_fields if field not in vat_entry]
                
                if missing_fields:
                    logger.warning(f"Pominięto wpis VAT z brakującymi polami: {missing_fields}")
                    continue
                
                # 3. Sprawdź i napraw stawkę VAT
                stawka = vat_entry['stawka']
                if not isinstance(stawka, str) or stawka not in ['A', 'B', 'C', 'D']:
                    # Spróbuj naprawić
                    if isinstance(stawka, str):
                        stawka_upper = stawka.upper()
                        if stawka_upper in ['A', 'B', 'C', 'D']:
                            vat_entry['stawka'] = stawka_upper
                        else:
                            logger.warning(f"Pominięto wpis VAT z niepoprawną stawką: {stawka}")
                            continue
                    else:
                        logger.warning(f"Pominięto wpis VAT z niepoprawną stawką: {stawka}")
                        continue
                
                # 4. Sprawdź i napraw wartości liczbowe
                for field in ['podstawa', 'kwota']:
                    value = vat_entry[field]
                    if isinstance(value, str):
                        try:
                            value = float(value.replace(',', '.').replace(' ', ''))
                            vat_entry[field] = round(value, 2)
                        except ValueError:
                            logger.warning(f"Pominięto wpis VAT z niepoprawną wartością {field}: {value}")
                            continue
                    elif not isinstance(value, (int, float)):
                        logger.warning(f"Pominięto wpis VAT z niepoprawną wartością {field}: {value}")
                        continue
                    else:
                        vat_entry[field] = round(float(value), 2)
                
                # 5. Dodaj procent VAT
                vat_percent = {
                    'A': 23,
                    'B': 8,
                    'C': 5,
                    'D': 0
                }[vat_entry['stawka']]
                
                vat_entry['procent'] = vat_percent
                
                # 6. Sprawdź spójność wartości
                expected_vat = round(vat_entry['podstawa'] * (vat_percent / 100), 2)
                actual_vat = vat_entry['kwota']
                
                if abs(expected_vat - actual_vat) > 0.01:  # Tolerancja na błędy zaokrągleń
                    logger.warning(
                        f"Niespójna kwota VAT dla stawki {vat_entry['stawka']}: "
                        f"oczekiwana {expected_vat}, rzeczywista {actual_vat}"
                    )
                
                valid_vat.append(vat_entry)
                
            except Exception as e:
                logger.error(f"Błąd podczas walidacji wpisu VAT: {str(e)}")
                continue
        
        return valid_vat
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych VAT: {str(e)}")
        return []

def _validate_and_repair_discounts(discounts: List[Dict]) -> List[Dict]:
    """
    Waliduje i naprawia dane rabatów.
    
    Args:
        discounts: Lista słowników z danymi rabatów
        
    Returns:
        Naprawiona lista danych rabatów
    """
    try:
        if not isinstance(discounts, list):
            logger.warning("Dane rabatów nie są listą, zwracam pustą listę")
            return []
        
        valid_discounts = []
        
        for discount in discounts:
            try:
                # 1. Sprawdź czy to słownik
                if not isinstance(discount, dict):
                    logger.warning(f"Pominięto niepoprawny rabat: {discount}")
                    continue
                
                # 2. Sprawdź wymagane pola
                required_fields = ['nazwa', 'wartosc']
                missing_fields = [field for field in required_fields if field not in discount]
                
                if missing_fields:
                    logger.warning(f"Pominięto rabat z brakującymi polami: {missing_fields}")
                    continue
                
                # 3. Sprawdź i napraw nazwę
                if not isinstance(discount['nazwa'], str) or not discount['nazwa'].strip():
                    logger.warning(f"Pominięto rabat z niepoprawną nazwą: {discount['nazwa']}")
                    continue
                
                # Usuń zbędne białe znaki
                discount['nazwa'] = discount['nazwa'].strip()
                
                # 4. Sprawdź i napraw wartość
                value = discount['wartosc']
                if isinstance(value, str):
                    try:
                        value = float(value.replace(',', '.').replace(' ', ''))
                        discount['wartosc'] = round(value, 2)
                    except ValueError:
                        logger.warning(f"Pominięto rabat z niepoprawną wartością: {value}")
                        continue
                elif not isinstance(value, (int, float)):
                    logger.warning(f"Pominięto rabat z niepoprawną wartością: {value}")
                    continue
                else:
                    discount['wartosc'] = round(float(value), 2)
                
                # 5. Sprawdź czy wartość jest dodatnia
                if discount['wartosc'] <= 0:
                    logger.warning(f"Pominięto rabat z nieujemną wartością: {discount['wartosc']}")
                    continue
                
                valid_discounts.append(discount)
                
            except Exception as e:
                logger.error(f"Błąd podczas walidacji rabatu: {str(e)}")
                continue
        
        return valid_discounts
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych rabatów: {str(e)}")
        return []

def _validate_and_repair_payment(payment_data: Dict) -> Dict:
    """
    Waliduje i naprawia dane płatności.
    
    Args:
        payment_data: Słownik z danymi płatności
        
    Returns:
        Naprawiony słownik z danymi płatności
    """
    try:
        if not isinstance(payment_data, dict):
            logger.warning("Dane płatności nie są słownikiem, zwracam pusty słownik")
            return {}
        
        # 1. Sprawdź wymagane pola
        required_fields = ['suma', 'metoda']
        missing_fields = [field for field in required_fields if field not in payment_data]
        
        if missing_fields:
            logger.warning(f"Brak wymaganych pól w danych płatności: {missing_fields}")
            return {}
        
        # 2. Sprawdź i napraw sumę
        total = payment_data['suma']
        if isinstance(total, str):
            try:
                total = float(total.replace(',', '.').replace(' ', ''))
                payment_data['suma'] = round(total, 2)
            except ValueError:
                logger.warning(f"Niepoprawna suma płatności: {total}")
                return {}
        elif not isinstance(total, (int, float)):
            logger.warning(f"Niepoprawna suma płatności: {total}")
            return {}
        else:
            payment_data['suma'] = round(float(total), 2)
        
        # 3. Sprawdź i napraw metodę płatności
        method = payment_data['metoda']
        if not isinstance(method, str) or not method.strip():
            logger.warning(f"Niepoprawna metoda płatności: {method}")
            return {}
        
        # Standaryzuj metodę płatności
        method_lower = method.lower().strip()
        if 'kart' in method_lower:
            payment_data['metoda'] = 'KARTA'
        elif 'got' in method_lower:
            payment_data['metoda'] = 'GOTÓWKA'
        elif 'blik' in method_lower:
            payment_data['metoda'] = 'BLIK'
        else:
            payment_data['metoda'] = 'INNA'
        
        # 4. Sprawdź i napraw resztę
        if 'reszta' in payment_data:
            change = payment_data['reszta']
            if isinstance(change, str):
                try:
                    change = float(change.replace(',', '.').replace(' ', ''))
                    payment_data['reszta'] = round(change, 2)
                except ValueError:
                    logger.warning(f"Niepoprawna reszta: {change}, usuwam pole")
                    del payment_data['reszta']
            elif not isinstance(change, (int, float)):
                logger.warning(f"Niepoprawna reszta: {change}, usuwam pole")
                del payment_data['reszta']
            else:
                payment_data['reszta'] = round(float(change), 2)
        
        # 5. Sprawdź i napraw dane VAT
        if 'vat' in payment_data:
            payment_data['vat'] = _validate_and_repair_vat(payment_data['vat'])
        
        # 6. Sprawdź spójność danych
        if 'vat' in payment_data:
            vat_total = sum(entry['kwota'] for entry in payment_data['vat'])
            if abs(vat_total - payment_data['suma']) > 0.01:  # Tolerancja na błędy zaokrągleń
                logger.warning(
                    f"Niespójna suma VAT: suma VAT {vat_total}, "
                    f"suma paragonu {payment_data['suma']}"
                )
        
        return payment_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych płatności: {str(e)}")
        return {}

def _validate_and_repair_store(store_data: Dict, detected_store_id: Optional[str] = None) -> Dict:
    """
    Waliduje i naprawia dane sklepu.
    
    Args:
        store_data: Słownik z danymi sklepu
        detected_store_id: Wykryty identyfikator sklepu
        
    Returns:
        Naprawiony słownik z danymi sklepu
    """
    try:
        if not isinstance(store_data, dict):
            logger.warning("Dane sklepu nie są słownikiem, zwracam pusty słownik")
            return {}
        
        # 1. Sprawdź wymagane pola
        required_fields = ['nazwa', 'adres_sklepu', 'nip']
        missing_fields = [field for field in required_fields if field not in store_data]
        
        if missing_fields:
            logger.warning(f"Brak wymaganych pól w danych sklepu: {missing_fields}")
            return {}
        
        # 2. Sprawdź i napraw nazwę
        name = store_data['nazwa']
        if not isinstance(name, str) or not name.strip():
            if detected_store_id:
                store_data['nazwa'] = detected_store_id.upper()
            else:
                logger.warning(f"Niepoprawna nazwa sklepu: {name}")
                return {}
        else:
            store_data['nazwa'] = name.strip()
        
        # 3. Sprawdź i napraw adres sklepu
        address = store_data['adres_sklepu']
        if not isinstance(address, str) or not address.strip():
            logger.warning(f"Niepoprawny adres sklepu: {address}")
            return {}
        else:
            # Usuń zbędne białe znaki i ujednolicaj format
            address = address.strip()
            address = re.sub(r'\s+', ' ', address)  # Zamień wielokrotne spacje na pojedyncze
            address = re.sub(r'ul\.\s*', 'ul. ', address)  # Ujednolicaj 'ul.'
            store_data['adres_sklepu'] = address
        
        # 4. Sprawdź i napraw NIP
        nip = store_data['nip']
        if isinstance(nip, str):
            # Usuń wszystko poza cyframi
            nip = re.sub(r'[^0-9]', '', nip)
            if len(nip) == 10:  # Polski NIP ma 10 cyfr
                store_data['nip'] = nip
            else:
                logger.warning(f"Niepoprawny NIP: {nip}")
                return {}
        else:
            logger.warning(f"Niepoprawny NIP: {nip}")
            return {}
        
        # 5. Sprawdź i napraw adres centrali
        if 'adres_centrali' in store_data:
            central_address = store_data['adres_centrali']
            if not isinstance(central_address, str) or not central_address.strip():
                del store_data['adres_centrali']
            else:
                # Usuń zbędne białe znaki i ujednolicaj format
                central_address = central_address.strip()
                central_address = re.sub(r'\s+', ' ', central_address)
                central_address = re.sub(r'ul\.\s*', 'ul. ', central_address)
                store_data['adres_centrali'] = central_address
        
        # 6. Dodaj domyślny adres centrali jeśli brak
        if 'adres_centrali' not in store_data:
            store_data['adres_centrali'] = {
                'LIDL': 'Lidl sp. z o.o. sp. k., ul. Poznańska 48, 62-080 Tarnowo Podgórne',
                'BIEDRONKA': 'Jeronimo Martins Polska S.A., ul. Żniwna 5, 62-025 Kostrzyn',
                'KAUFLAND': 'Kaufland Polska Markety sp. z o.o. sp.k., ul. Armii Krajowej 47, 50-541 Wrocław',
                'AUCHAN': 'Auchan Polska sp. z o.o., ul. Puławska 46, 05-500 Piaseczno'
            }.get(store_data['nazwa'].upper(), '')
        
        return store_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych sklepu: {str(e)}")
        return {}

def _validate_and_repair_datetime(receipt_data: Dict) -> Dict:
    """
    Waliduje i naprawia dane daty i godziny.
    
    Args:
        receipt_data: Słownik z danymi paragonu
        
    Returns:
        Naprawiony słownik z danymi paragonu
    """
    try:
        # 1. Sprawdź czy wymagane pola istnieją
        required_fields = ['data', 'godzina']
        missing_fields = [field for field in required_fields if field not in receipt_data]
        
        if missing_fields:
            logger.warning(f"Brak wymaganych pól daty/godziny: {missing_fields}")
            # Spróbuj wydobyć datę z metadanych pliku
            file_path = receipt_data.get('metadata', {}).get('source_file')
            if file_path:
                file_stat = Path(file_path).stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                receipt_data['data'] = file_time.strftime('%Y-%m-%d')
                receipt_data['godzina'] = file_time.strftime('%H:%M')
                logger.info("Użyto daty modyfikacji pliku jako daty paragonu")
            else:
                # Użyj bieżącej daty i godziny
                now = datetime.now()
                receipt_data['data'] = now.strftime('%Y-%m-%d')
                receipt_data['godzina'] = now.strftime('%H:%M')
                logger.warning("Użyto bieżącej daty i godziny")
        
        # 2. Sprawdź i napraw datę
        date_str = receipt_data['data']
        if isinstance(date_str, str):
            try:
                # Usuń zbędne znaki
                date_str = re.sub(r'[^0-9\-\./]', '', date_str)
                
                # Spróbuj różne formaty daty
                for date_format in ['%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y', '%d-%m-%Y']:
                    try:
                        parsed_date = datetime.strptime(date_str, date_format)
                        receipt_data['data'] = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Nie udało się sparsować daty: {date_str}")
                    
            except Exception as e:
                logger.warning(f"Błąd podczas parsowania daty: {str(e)}")
                # Użyj bieżącej daty
                receipt_data['data'] = datetime.now().strftime('%Y-%m-%d')
        else:
            logger.warning(f"Niepoprawny format daty: {date_str}")
            receipt_data['data'] = datetime.now().strftime('%Y-%m-%d')
        
        # 3. Sprawdź i napraw godzinę
        time_str = receipt_data['godzina']
        if isinstance(time_str, str):
            try:
                # Usuń zbędne znaki
                time_str = re.sub(r'[^0-9\:]', '', time_str)
                
                # Spróbuj różne formaty godziny
                for time_format in ['%H:%M', '%H.%M', '%H:%M:%S']:
                    try:
                        parsed_time = datetime.strptime(time_str, time_format)
                        receipt_data['godzina'] = parsed_time.strftime('%H:%M')
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Nie udało się sparsować godziny: {time_str}")
                    
            except Exception as e:
                logger.warning(f"Błąd podczas parsowania godziny: {str(e)}")
                # Użyj bieżącej godziny
                receipt_data['godzina'] = datetime.now().strftime('%H:%M')
        else:
            logger.warning(f"Niepoprawny format godziny: {time_str}")
            receipt_data['godzina'] = datetime.now().strftime('%H:%M')
        
        # 4. Sprawdź czy data nie jest z przyszłości
        try:
            receipt_datetime = datetime.strptime(
                f"{receipt_data['data']} {receipt_data['godzina']}",
                '%Y-%m-%d %H:%M'
            )
            
            if receipt_datetime > datetime.now():
                logger.warning("Data paragonu jest z przyszłości, używam bieżącej daty")
                now = datetime.now()
                receipt_data['data'] = now.strftime('%Y-%m-%d')
                receipt_data['godzina'] = now.strftime('%H:%M')
                
        except Exception as e:
            logger.error(f"Błąd podczas walidacji daty i godziny: {str(e)}")
        
        return receipt_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych daty i godziny: {str(e)}")
        # Użyj bieżącej daty i godziny
        now = datetime.now()
        receipt_data['data'] = now.strftime('%Y-%m-%d')
        receipt_data['godzina'] = now.strftime('%H:%M')
        return receipt_data

def _validate_and_repair_loyalty_card(receipt_data: Dict) -> Dict:
    """
    Waliduje i naprawia dane karty lojalnościowej.
    
    Args:
        receipt_data: Słownik z danymi paragonu
        
    Returns:
        Naprawiony słownik z danymi paragonu
    """
    try:
        # 1. Sprawdź czy pole karty lojalnościowej istnieje
        if 'karta_lojalnosciowa' not in receipt_data:
            return receipt_data
        
        card_data = receipt_data['karta_lojalnosciowa']
        
        # 2. Sprawdź czy dane karty są słownikiem
        if not isinstance(card_data, dict):
            logger.warning("Dane karty lojalnościowej nie są słownikiem, usuwam pole")
            del receipt_data['karta_lojalnosciowa']
            return receipt_data
        
        # 3. Sprawdź wymagane pola
        required_fields = ['numer', 'typ']
        missing_fields = [field for field in required_fields if field not in card_data]
        
        if missing_fields:
            logger.warning(f"Brak wymaganych pól w danych karty: {missing_fields}")
            del receipt_data['karta_lojalnosciowa']
            return receipt_data
        
        # 4. Sprawdź i napraw numer karty
        card_number = card_data['numer']
        if isinstance(card_number, str):
            # Usuń wszystko poza cyframi
            card_number = re.sub(r'[^0-9]', '', card_number)
            if len(card_number) >= 8:  # Minimalna długość numeru karty
                card_data['numer'] = card_number
            else:
                logger.warning(f"Niepoprawny numer karty: {card_number}")
                del receipt_data['karta_lojalnosciowa']
                return receipt_data
        else:
            logger.warning(f"Niepoprawny format numeru karty: {card_number}")
            del receipt_data['karta_lojalnosciowa']
            return receipt_data
        
        # 5. Sprawdź i napraw typ karty
        card_type = card_data['typ']
        if isinstance(card_type, str):
            card_type = card_type.strip().upper()
            # Standaryzuj nazwy kart
            if 'LIDL' in card_type:
                card_data['typ'] = 'LIDL PLUS'
            elif 'BIEDRONKA' in card_type or 'MOJA BIEDRONKA' in card_type:
                card_data['typ'] = 'MOJA BIEDRONKA'
            elif 'KAUFLAND' in card_type:
                card_data['typ'] = 'KAUFLAND CARD'
            elif 'AUCHAN' in card_type:
                card_data['typ'] = 'SKARBONKA'
            else:
                card_data['typ'] = 'INNA'
        else:
            logger.warning(f"Niepoprawny format typu karty: {card_type}")
            del receipt_data['karta_lojalnosciowa']
            return receipt_data
        
        # 6. Sprawdź i napraw punkty
        if 'punkty' in card_data:
            points = card_data['punkty']
            if isinstance(points, str):
                try:
                    points = float(points.replace(',', '.').replace(' ', ''))
                    card_data['punkty'] = round(points, 2)
                except ValueError:
                    logger.warning(f"Niepoprawna wartość punktów: {points}, usuwam pole")
                    del card_data['punkty']
            elif not isinstance(points, (int, float)):
                logger.warning(f"Niepoprawna wartość punktów: {points}, usuwam pole")
                del card_data['punkty']
            else:
                card_data['punkty'] = round(float(points), 2)
        
        # 7. Sprawdź i napraw rabat
        if 'rabat' in card_data:
            discount = card_data['rabat']
            if isinstance(discount, str):
                try:
                    discount = float(discount.replace(',', '.').replace(' ', ''))
                    card_data['rabat'] = round(discount, 2)
                except ValueError:
                    logger.warning(f"Niepoprawna wartość rabatu: {discount}, usuwam pole")
                    del card_data['rabat']
            elif not isinstance(discount, (int, float)):
                logger.warning(f"Niepoprawna wartość rabatu: {discount}, usuwam pole")
                del card_data['rabat']
            else:
                card_data['rabat'] = round(float(discount), 2)
        
        receipt_data['karta_lojalnosciowa'] = card_data
        return receipt_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych karty lojalnościowej: {str(e)}")
        if 'karta_lojalnosciowa' in receipt_data:
            del receipt_data['karta_lojalnosciowa']
        return receipt_data

def _validate_and_repair_coupons(receipt_data: Dict) -> Dict:
    """
    Waliduje i naprawia dane użytych kuponów.
    
    Args:
        receipt_data: Słownik z danymi paragonu
        
    Returns:
        Naprawiony słownik z danymi paragonu
    """
    try:
        # 1. Sprawdź czy pole kuponów istnieje
        if 'kupony' not in receipt_data:
            return receipt_data
        
        coupons = receipt_data['kupony']
        
        # 2. Sprawdź czy dane kuponów są listą
        if not isinstance(coupons, list):
            logger.warning("Dane kuponów nie są listą, usuwam pole")
            del receipt_data['kupony']
            return receipt_data
        
        valid_coupons = []
        
        for coupon in coupons:
            try:
                # 3. Sprawdź czy kupon jest słownikiem
                if not isinstance(coupon, dict):
                    logger.warning(f"Pominięto niepoprawny kupon: {coupon}")
                    continue
                
                # 4. Sprawdź wymagane pola
                required_fields = ['kod', 'opis', 'wartosc']
                missing_fields = [field for field in required_fields if field not in coupon]
                
                if missing_fields:
                    logger.warning(f"Pominięto kupon z brakującymi polami: {missing_fields}")
                    continue
                
                # 5. Sprawdź i napraw kod kuponu
                code = coupon['kod']
                if not isinstance(code, str) or not code.strip():
                    logger.warning(f"Pominięto kupon z niepoprawnym kodem: {code}")
                    continue
                
                # Usuń zbędne białe znaki i ujednolicaj format
                coupon['kod'] = code.strip().upper()
                
                # 6. Sprawdź i napraw opis
                description = coupon['opis']
                if not isinstance(description, str) or not description.strip():
                    logger.warning(f"Pominięto kupon z niepoprawnym opisem: {description}")
                    continue
                
                # Usuń zbędne białe znaki i ujednolicaj format
                coupon['opis'] = description.strip()
                
                # 7. Sprawdź i napraw wartość
                value = coupon['wartosc']
                if isinstance(value, str):
                    try:
                        value = float(value.replace(',', '.').replace(' ', ''))
                        coupon['wartosc'] = round(value, 2)
                    except ValueError:
                        logger.warning(f"Pominięto kupon z niepoprawną wartością: {value}")
                        continue
                elif not isinstance(value, (int, float)):
                    logger.warning(f"Pominięto kupon z niepoprawną wartością: {value}")
                    continue
                else:
                    coupon['wartosc'] = round(float(value), 2)
                
                # 8. Sprawdź czy wartość jest dodatnia
                if coupon['wartosc'] <= 0:
                    logger.warning(f"Pominięto kupon z nieujemną wartością: {coupon['wartosc']}")
                    continue
                
                # 9. Sprawdź i napraw datę ważności
                if 'data_waznosci' in coupon:
                    expiry_date = coupon['data_waznosci']
                    if isinstance(expiry_date, str):
                        try:
                            # Usuń zbędne znaki
                            expiry_date = re.sub(r'[^0-9\-\./]', '', expiry_date)
                            
                            # Spróbuj różne formaty daty
                            for date_format in ['%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y', '%d-%m-%Y']:
                                try:
                                    parsed_date = datetime.strptime(expiry_date, date_format)
                                    coupon['data_waznosci'] = parsed_date.strftime('%Y-%m-%d')
                                    break
                                except ValueError:
                                    continue
                            else:
                                logger.warning(f"Niepoprawna data ważności: {expiry_date}, usuwam pole")
                                del coupon['data_waznosci']
                                
                        except Exception as e:
                            logger.warning(f"Błąd podczas parsowania daty ważności: {str(e)}")
                            del coupon['data_waznosci']
                    else:
                        logger.warning(f"Niepoprawny format daty ważności: {expiry_date}")
                        del coupon['data_waznosci']
                
                valid_coupons.append(coupon)
                
            except Exception as e:
                logger.error(f"Błąd podczas walidacji kuponu: {str(e)}")
                continue
        
        if valid_coupons:
            receipt_data['kupony'] = valid_coupons
        else:
            del receipt_data['kupony']
        
        return receipt_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych kuponów: {str(e)}")
        if 'kupony' in receipt_data:
            del receipt_data['kupony']
        return receipt_data

def _validate_and_repair_products(receipt_data: Dict) -> Dict:
    """
    Waliduje i naprawia dane produktów.
    
    Args:
        receipt_data: Słownik z danymi paragonu
        
    Returns:
        Naprawiony słownik z danymi paragonu
    """
    try:
        # 1. Sprawdź czy pole produktów istnieje
        if 'produkty' not in receipt_data:
            logger.warning("Brak produktów w danych paragonu")
            return receipt_data
        
        products = receipt_data['produkty']
        
        # 2. Sprawdź czy dane produktów są listą
        if not isinstance(products, list):
            logger.warning("Dane produktów nie są listą, usuwam pole")
            del receipt_data['produkty']
            return receipt_data
        
        valid_products = []
        
        for product in products:
            try:
                # 3. Sprawdź czy produkt jest słownikiem
                if not isinstance(product, dict):
                    logger.warning(f"Pominięto niepoprawny produkt: {product}")
                    continue
                
                # 4. Sprawdź wymagane pola
                required_fields = ['nazwa', 'ilosc', 'suma']
                missing_fields = [field for field in required_fields if field not in product]
                
                if missing_fields:
                    logger.warning(f"Pominięto produkt z brakującymi polami: {missing_fields}")
                    continue
                
                # 5. Sprawdź i napraw nazwę
                name = product['nazwa']
                if not isinstance(name, str) or not name.strip():
                    logger.warning(f"Pominięto produkt z niepoprawną nazwą: {name}")
                    continue
                
                # Usuń zbędne białe znaki i ujednolicaj format
                product['nazwa'] = name.strip()
                
                # 6. Sprawdź i napraw ilość
                quantity = product['ilosc']
                if isinstance(quantity, str):
                    try:
                        quantity = float(quantity.replace(',', '.').replace(' ', ''))
                        product['ilosc'] = round(quantity, 3)  # 3 miejsca po przecinku dla wag
                    except ValueError:
                        logger.warning(f"Pominięto produkt z niepoprawną ilością: {quantity}")
                        continue
                elif not isinstance(quantity, (int, float)):
                    logger.warning(f"Pominięto produkt z niepoprawną ilością: {quantity}")
                    continue
                else:
                    product['ilosc'] = round(float(quantity), 3)
                
                # 7. Sprawdź i napraw sumę
                total = product['suma']
                if isinstance(total, str):
                    try:
                        total = float(total.replace(',', '.').replace(' ', ''))
                        product['suma'] = round(total, 2)
                    except ValueError:
                        logger.warning(f"Pominięto produkt z niepoprawną sumą: {total}")
                        continue
                elif not isinstance(total, (int, float)):
                    logger.warning(f"Pominięto produkt z niepoprawną sumą: {total}")
                    continue
                else:
                    product['suma'] = round(float(total), 2)
                
                # 8. Sprawdź i napraw jednostkę
                if 'jednostka' in product:
                    unit = product['jednostka']
                    if isinstance(unit, str):
                        unit = unit.strip().lower()
                        # Standaryzuj jednostki
                        if unit in ['szt', 'szt.', 'sztuk', 'sztuka']:
                            product['jednostka'] = 'szt'
                        elif unit in ['kg', 'kilo', 'kilogram']:
                            product['jednostka'] = 'kg'
                        elif unit in ['g', 'gram']:
                            product['jednostka'] = 'g'
                            # Konwertuj gramy na kilogramy
                            product['ilosc'] = round(product['ilosc'] / 1000, 3)
                            product['jednostka'] = 'kg'
                        elif unit in ['l', 'litr']:
                            product['jednostka'] = 'l'
                        elif unit in ['ml', 'mililitr']:
                            product['jednostka'] = 'ml'
                            # Konwertuj mililitry na litry
                            product['ilosc'] = round(product['ilosc'] / 1000, 3)
                            product['jednostka'] = 'l'
                        elif unit in ['opak', 'opak.', 'opakowanie']:
                            product['jednostka'] = 'opak'
                        else:
                            product['jednostka'] = 'szt'
                    else:
                        product['jednostka'] = 'szt'
                else:
                    product['jednostka'] = 'szt'
                
                # 9. Sprawdź i napraw cenę jednostkową
                if 'cena_jednostkowa' in product:
                    unit_price = product['cena_jednostkowa']
                    if isinstance(unit_price, str):
                        try:
                            unit_price = float(unit_price.replace(',', '.').replace(' ', ''))
                            product['cena_jednostkowa'] = round(unit_price, 2)
                        except ValueError:
                            logger.warning(f"Usuwam niepoprawną cenę jednostkową: {unit_price}")
                            del product['cena_jednostkowa']
                    elif not isinstance(unit_price, (int, float)):
                        logger.warning(f"Usuwam niepoprawną cenę jednostkową: {unit_price}")
                        del product['cena_jednostkowa']
                    else:
                        product['cena_jednostkowa'] = round(float(unit_price), 2)
                
                # 10. Sprawdź i napraw rabat
                if 'rabat' in product:
                    discount = product['rabat']
                    if isinstance(discount, str):
                        try:
                            discount = float(discount.replace(',', '.').replace(' ', ''))
                            product['rabat'] = round(discount, 2)
                        except ValueError:
                            logger.warning(f"Usuwam niepoprawny rabat: {discount}")
                            del product['rabat']
                    elif not isinstance(discount, (int, float)):
                        logger.warning(f"Usuwam niepoprawny rabat: {discount}")
                        del product['rabat']
                    else:
                        product['rabat'] = round(float(discount), 2)
                
                # 11. Sprawdź i napraw stawkę VAT
                if 'stawka_vat' in product:
                    vat_rate = product['stawka_vat']
                    if isinstance(vat_rate, str):
                        vat_rate = vat_rate.strip().upper()
                        if vat_rate in ['A', 'B', 'C', 'D']:
                            product['stawka_vat'] = vat_rate
                        else:
                            logger.warning(f"Usuwam niepoprawną stawkę VAT: {vat_rate}")
                            del product['stawka_vat']
                    else:
                        logger.warning(f"Usuwam niepoprawną stawkę VAT: {vat_rate}")
                        del product['stawka_vat']
                
                # 12. Sprawdź spójność danych
                if 'cena_jednostkowa' in product:
                    expected_total = round(product['ilosc'] * product['cena_jednostkowa'], 2)
                    if 'rabat' in product:
                        expected_total -= product['rabat']
                    
                    if abs(expected_total - product['suma']) > 0.01:  # Tolerancja na błędy zaokrągleń
                        logger.warning(
                            f"Niespójna suma dla produktu {product['nazwa']}: "
                            f"oczekiwana {expected_total}, rzeczywista {product['suma']}"
                        )
                
                valid_products.append(product)
                
            except Exception as e:
                logger.error(f"Błąd podczas walidacji produktu: {str(e)}")
                continue
        
        if valid_products:
            receipt_data['produkty'] = valid_products
        else:
            logger.warning("Brak poprawnych produktów, usuwam pole")
            del receipt_data['produkty']
        
        return receipt_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych produktów: {str(e)}")
        if 'produkty' in receipt_data:
            del receipt_data['produkty']
        return receipt_data

def _validate_and_repair_control_numbers(receipt_data: Dict) -> Dict:
    """
    Waliduje i naprawia dane numerów kontrolnych.
    
    Args:
        receipt_data: Słownik z danymi paragonu
        
    Returns:
        Naprawiony słownik z danymi paragonu
    """
    try:
        # 1. Sprawdź czy pole numerów kontrolnych istnieje
        if 'numery_kontrolne' not in receipt_data:
            return receipt_data
        
        control_numbers = receipt_data['numery_kontrolne']
        
        # 2. Sprawdź czy dane numerów kontrolnych są słownikiem
        if not isinstance(control_numbers, dict):
            logger.warning("Dane numerów kontrolnych nie są słownikiem, usuwam pole")
            del receipt_data['numery_kontrolne']
            return receipt_data
        
        # 3. Sprawdź i napraw numer paragonu
        if 'numer_paragonu' in control_numbers:
            receipt_number = control_numbers['numer_paragonu']
            if isinstance(receipt_number, str):
                # Usuń zbędne białe znaki i ujednolicaj format
                receipt_number = receipt_number.strip()
                if receipt_number:
                    control_numbers['numer_paragonu'] = receipt_number
                else:
                    logger.warning("Usuwam pusty numer paragonu")
                    del control_numbers['numer_paragonu']
            else:
                logger.warning(f"Usuwam niepoprawny numer paragonu: {receipt_number}")
                del control_numbers['numer_paragonu']
        
        # 4. Sprawdź i napraw numer kasy
        if 'numer_kasy' in control_numbers:
            register_number = control_numbers['numer_kasy']
            if isinstance(register_number, str):
                # Usuń wszystko poza cyframi
                register_number = re.sub(r'[^0-9]', '', register_number)
                if register_number:
                    control_numbers['numer_kasy'] = register_number
                else:
                    logger.warning("Usuwam pusty numer kasy")
                    del control_numbers['numer_kasy']
            else:
                logger.warning(f"Usuwam niepoprawny numer kasy: {register_number}")
                del control_numbers['numer_kasy']
        
        # 5. Sprawdź i napraw numer unikatowy
        if 'numer_unikatowy' in control_numbers:
            unique_number = control_numbers['numer_unikatowy']
            if isinstance(unique_number, str):
                # Usuń zbędne białe znaki i ujednolicaj format
                unique_number = unique_number.strip()
                if unique_number:
                    control_numbers['numer_unikatowy'] = unique_number
                else:
                    logger.warning("Usuwam pusty numer unikatowy")
                    del control_numbers['numer_unikatowy']
            else:
                logger.warning(f"Usuwam niepoprawny numer unikatowy: {unique_number}")
                del control_numbers['numer_unikatowy']
        
        # 6. Sprawdź i napraw numer fiskalny
        if 'numer_fiskalny' in control_numbers:
            fiscal_number = control_numbers['numer_fiskalny']
            if isinstance(fiscal_number, str):
                # Usuń zbędne białe znaki i ujednolicaj format
                fiscal_number = fiscal_number.strip()
                if fiscal_number:
                    control_numbers['numer_fiskalny'] = fiscal_number
                else:
                    logger.warning("Usuwam pusty numer fiskalny")
                    del control_numbers['numer_fiskalny']
            else:
                logger.warning(f"Usuwam niepoprawny numer fiskalny: {fiscal_number}")
                del control_numbers['numer_fiskalny']
        
        # 7. Sprawdź czy pozostały jakieś numery
        if not control_numbers:
            logger.warning("Brak poprawnych numerów kontrolnych, usuwam pole")
            del receipt_data['numery_kontrolne']
        else:
            receipt_data['numery_kontrolne'] = control_numbers
        
        return receipt_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych numerów kontrolnych: {str(e)}")
        if 'numery_kontrolne' in receipt_data:
            del receipt_data['numery_kontrolne']
        return receipt_data

def _validate_and_repair_cashier(receipt_data: Dict) -> Dict:
    """
    Waliduje i naprawia dane kasjera.
    
    Args:
        receipt_data: Słownik z danymi paragonu
        
    Returns:
        Naprawiony słownik z danymi paragonu
    """
    try:
        # 1. Sprawdź czy pole kasjera istnieje
        if 'kasjer' not in receipt_data:
            return receipt_data
        
        cashier_data = receipt_data['kasjer']
        
        # 2. Sprawdź czy dane kasjera są słownikiem
        if not isinstance(cashier_data, dict):
            logger.warning("Dane kasjera nie są słownikiem, usuwam pole")
            del receipt_data['kasjer']
            return receipt_data
        
        # 3. Sprawdź i napraw numer kasjera
        if 'numer' in cashier_data:
            cashier_number = cashier_data['numer']
            if isinstance(cashier_number, str):
                # Usuń wszystko poza cyframi
                cashier_number = re.sub(r'[^0-9]', '', cashier_number)
                if cashier_number:
                    cashier_data['numer'] = cashier_number
                else:
                    logger.warning("Usuwam pusty numer kasjera")
                    del cashier_data['numer']
            else:
                logger.warning(f"Usuwam niepoprawny numer kasjera: {cashier_number}")
                del cashier_data['numer']
        
        # 4. Sprawdź i napraw imię
        if 'imie' in cashier_data:
            name = cashier_data['imie']
            if isinstance(name, str):
                # Usuń zbędne białe znaki i ujednolicaj format
                name = name.strip()
                if name:
                    # Pierwsza litera wielka, reszta małe
                    cashier_data['imie'] = name.capitalize()
                else:
                    logger.warning("Usuwam puste imię kasjera")
                    del cashier_data['imie']
            else:
                logger.warning(f"Usuwam niepoprawne imię kasjera: {name}")
                del cashier_data['imie']
        
        # 5. Sprawdź czy pozostały jakieś dane
        if not cashier_data:
            logger.warning("Brak poprawnych danych kasjera, usuwam pole")
            del receipt_data['kasjer']
        else:
            receipt_data['kasjer'] = cashier_data
        
        return receipt_data
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji danych kasjera: {str(e)}")
        if 'kasjer' in receipt_data:
            del receipt_data['kasjer']
        return receipt_data

def process_receipt(file_path: Path, prompt_file: Path, model: str, url: str) -> Dict:
    """
    Przetwarza paragon i zwraca dane w formacie JSON.
    
    Args:
        file_path: Ścieżka do pliku paragonu
        prompt_file: Ścieżka do pliku z promptem
        model: Nazwa modelu do użycia
        url: URL serwera Ollama
        
    Returns:
        Słownik z danymi paragonu
    """
    processing_start = time.time()
    
    try:
        # 1. Ekstrakcja tekstu
        start_time = time.time()
        receipt_text = extract_text_from_file(file_path)
        ocr_time = time.time() - start_time
        
        # Log OCR output
        logger.debug("OCR output:")
        logger.debug("-" * 80)
        logger.debug(receipt_text)
        logger.debug("-" * 80)
        
        # 2. Wykryj sklep
        store_id, store_confidence = detect_store(receipt_text)
        
        # 3. Wybierz prompt
        prompt_text, used_prompt_file = get_store_prompt(store_id, prompt_file)
        
        # 4. Wstaw tekst paragonu do promptu
        prompt_text = prompt_text.replace('{{TEKST_PARAGONU}}', receipt_text)
        
        # Log prompt
        logger.debug("Prompt:")
        logger.debug("-" * 80)
        logger.debug(prompt_text)
        logger.debug("-" * 80)
        
        # 5. Wyślij zapytanie do modelu
        start_time = time.time()
        response_text = query_ollama(url, model, prompt_text)
        model_time = time.time() - start_time
        
        # Log model response
        logger.debug("Model response:")
        logger.debug("-" * 80)
        logger.debug(response_text)
        logger.debug("-" * 80)
        
        # 6. Parsuj odpowiedź JSON
        receipt_data = json.loads(response_text)
        
        # 7. Waliduj i napraw dane sklepu
        receipt_data = _validate_and_repair_store(receipt_data, store_id)
        
        # 8. Waliduj i napraw dane VAT
        if 'platnosc' in receipt_data and 'vat' in receipt_data['platnosc']:
            receipt_data['platnosc']['vat'] = _validate_and_repair_vat(receipt_data['platnosc']['vat'])
        
        # 9. Waliduj i napraw dane płatności
        if 'platnosc' in receipt_data:
            receipt_data['platnosc'] = _validate_and_repair_payment(receipt_data['platnosc'])
        
        # 10. Waliduj i napraw dane daty i godziny
        receipt_data = _validate_and_repair_datetime(receipt_data)
        
        # 11. Waliduj i napraw dane karty lojalnościowej
        receipt_data = _validate_and_repair_loyalty_card(receipt_data)
        
        # 12. Waliduj i napraw dane kuponów
        receipt_data = _validate_and_repair_coupons(receipt_data)
        
        # 13. Waliduj i napraw dane produktów
        receipt_data = _validate_and_repair_products(receipt_data)
        
        # 14. Waliduj i napraw dane numerów kontrolnych
        receipt_data = _validate_and_repair_control_numbers(receipt_data)
        
        # 15. Waliduj i napraw dane kasjera
        receipt_data = _validate_and_repair_cashier(receipt_data)
        
        # 16. Wzbogać dane o analizę produktów
        try:
            if 'produkty' in receipt_data:
                enriched_products = analyze_receipt_products(
                    receipt_data['produkty'],
                    receipt_text,
                    url,
                    model
                )
                receipt_data['produkty'] = enriched_products
            
            # 17. Dodaj metadane
            receipt_data['metadata'] = {
                'source_file': str(file_path),
                'file_size': file_path.stat().st_size,
                'detected_store': store_id,
                'store_confidence': store_confidence,
                'used_prompt': str(used_prompt_file),
                'model': model,
                'processing_times': {
                    'ocr': round(ocr_time, 2),
                    'model': round(model_time, 2),
                    'total': round(time.time() - processing_start, 2)
                },
                'extracted_text_length': len(receipt_text),
                'processed_at': datetime.now().isoformat()
            }
            
            logger.info(f"Przetworzono paragon w {receipt_data['metadata']['processing_times']['total']:.2f} sekund")
            return receipt_data
            
        except Exception as e:
            raise ValidationError(f"Błąd podczas wzbogacania danych: {str(e)}")
        
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania paragonu {file_path}: {str(e)}")
        raise

# Klasy wyjątków
class OCRError(Exception):
    """Błąd podczas OCR"""
    pass

class ModelError(Exception):
    """Błąd podczas komunikacji z modelem"""
    pass

class ValidationError(Exception):
    """Błąd podczas walidacji danych"""
    pass

def main():
    """
    Główna funkcja programu.
    """
    parser = argparse.ArgumentParser(
        description='Przetwarzanie paragonów z OCR i LLM',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Argumenty wymagane
    parser.add_argument(
        'file_path',
        type=str,
        help='Ścieżka do pliku paragonu (PDF lub obraz)'
    )
    
    # Argumenty opcjonalne
    parser.add_argument(
        '--prompt',
        type=str,
        default=DEFAULT_SYSTEM_PROMPT_FILE,
        help='Ścieżka do pliku z promptem systemowym'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_OLLAMA_MODEL,
        help='Nazwa modelu Ollama do użycia'
    )
    parser.add_argument(
        '--url',
        type=str,
        default=DEFAULT_OLLAMA_URL,
        help='URL serwera Ollama'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Ścieżka do pliku wyjściowego JSON (domyślnie: stdout)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Włącz tryb debugowania (więcej logów)'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Wyłącz kolorowe logi'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Zapisz logi do pliku'
    )
    
    args = parser.parse_args()
    
    # Konfiguracja logowania
    log_level = logging.DEBUG if args.debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if not args.no_color:
        try:
            import coloredlogs
            coloredlogs.install(
                level=log_level,
                fmt=log_format
            )
        except ImportError:
            logging.basicConfig(
                level=log_level,
                format=log_format
            )
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format
        )
    
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    try:
        # Sprawdź czy plik istnieje
        file_path = Path(args.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku: {args.file_path}")
            
        # Sprawdź rozszerzenie pliku
        if file_path.suffix.lower() not in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            raise ValueError(
                f"Nieobsługiwany format pliku: {file_path.suffix}. "
                "Obsługiwane formaty: PDF, JPG, JPEG, PNG, TIFF, BMP"
            )
        
        # Przetwórz paragon
        result = process_receipt(
            file_path=file_path,
            prompt_file=Path(args.prompt),
            model=args.model,
            url=args.url
        )
        
        # Zapisz wynik
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Zapisano wynik do: {output_path}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except FileNotFoundError as e:
        logger.error(f"Błąd: {str(e)}")
        sys.exit(1)
    except OCRError as e:
        logger.error(f"Błąd OCR: {str(e)}")
        sys.exit(2)
    except ModelError as e:
        logger.error(f"Błąd modelu: {str(e)}")
        sys.exit(3)
    except ValidationError as e:
        logger.error(f"Błąd walidacji: {str(e)}")
        sys.exit(4)
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(5)

if __name__ == '__main__':
    main() 