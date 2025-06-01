#!/usr/bin/env python3
"""
Moduł analizy i standaryzacji produktów z paragonów
"""

import json
import requests
from typing import Dict, List, Optional, Union
import logging
import time

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Stałe kategorii produktów
PRODUCT_CATEGORIES = {
    'NABIAŁ': ['mleko', 'ser', 'jogurt', 'śmietana', 'masło', 'margaryna', 'twaróg'],
    'MIĘSO': ['mięso', 'drób', 'wędlina', 'kiełbasa', 'szynka', 'parówki'],
    'WARZYWA': ['warzywa', 'marchew', 'ziemniaki', 'cebula', 'pomidor', 'ogórek'],
    'OWOCE': ['owoce', 'jabłka', 'banany', 'pomarańcze', 'cytryny'],
    'NAPOJE': ['napój', 'woda', 'sok', 'cola', 'piwo', 'kawa', 'herbata'],
    'PIECZYWO': ['chleb', 'bułka', 'bagietka', 'rogal', 'drożdżówka'],
    'SŁODYCZE': ['cukierki', 'czekolada', 'ciastka', 'batonik', 'wafelek'],
    'PRZEKĄSKI': ['chipsy', 'paluszki', 'orzeszki', 'krakersy'],
    'MROŻONKI': ['mrożonki', 'lody', 'mrożona pizza', 'mrożone warzywa'],
    'CHEMIA': ['proszek', 'płyn', 'mydło', 'szampon', 'pasta'],
    'INNE': []  # Kategoria domyślna
}

# Słowa kluczowe wskazujące na mrożonki
FROZEN_KEYWORDS = [
    'mrożon', 'lód', 'lody', 'zamrożon', 'schłodzon',
    'mroż.', 'lod.', 'zamroż.', 'schłodz.'
]

class ModelError(Exception):
    """Błąd modelu LLM."""
    pass

def _validate_product(product: Dict) -> Dict:
    """
    Waliduje dane produktu.
    
    Args:
        product: Słownik z danymi produktu
        
    Returns:
        Zwalidowany słownik produktu
        
    Raises:
        ValueError: Jeśli brakuje wymaganych pól
    """
    required_fields = ["nazwa", "ilosc", "suma"]
    missing_fields = [field for field in required_fields if field not in product]
    
    if missing_fields:
        logger.warning(f"Brak wymaganych pól w produkcie: {', '.join(missing_fields)}")
        raise ValueError(f"Brak wymaganych pól: {', '.join(missing_fields)}")
    
    return {
        "nazwa": product["nazwa"],
        "ilosc": float(product["ilosc"]),
        "suma": float(product["suma"])
    }

def _get_ai_product_analysis(
    product: Dict,
    ollama_url: str,
    model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
) -> Dict:
    """
    Analizuje produkt używając modelu LLM.
    
    Args:
        product: Słownik z danymi produktu
        ollama_url: URL API Ollama
        model: Nazwa modelu do użycia
        
    Returns:
        Słownik z analizą AI
        
    Raises:
        ModelError: W przypadku błędu modelu
    """
    try:
        # Upewnij się, że URL kończy się na /api/generate
        if not ollama_url.endswith('/api/generate'):
            ollama_url = ollama_url.rstrip('/') + '/api/generate'
            
        prompt = f"""
        Przeanalizuj następujący produkt z paragonu:
        
        {product['nazwa']}
        
        Zwróć informacje w formacie JSON:
        {{
            "standardized_name": "ustandaryzowana nazwa produktu",
            "category": "kategoria produktu (NABIAŁ/PIECZYWO/MIĘSO/WARZYWA/OWOCE/NAPOJE/MROŻONKI/INNE)",
            "is_frozen": true/false (czy to jest produkt mrożony)
        }}
        """
        
        response = requests.post(
            ollama_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 1024
                }
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise ModelError(f"API zwróciło błąd: {response.status_code}")
            
        result = response.json()
        if "response" not in result:
            raise ModelError("Brak odpowiedzi w wyniku API")
            
        # Znajdź i wytnij JSON z odpowiedzi
        response_text = result["response"]
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ModelError("Nie znaleziono poprawnej struktury JSON w odpowiedzi")
            
        response_text = response_text[start_idx:end_idx + 1]
        
        try:
            analysis = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ModelError(f"Nie udało się sparsować odpowiedzi JSON: {str(e)}")
            
        # Walidacja wymaganych pól
        required_fields = ["standardized_name", "category", "is_frozen"]
        missing_fields = [field for field in required_fields if field not in analysis]
        
        if missing_fields:
            raise ModelError(f"Brak wymaganych pól w odpowiedzi: {', '.join(missing_fields)}")
            
        logger.info(f"Pomyślnie przeanalizowano produkt: {product['nazwa']}")
        return analysis
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd połączenia z API: {str(e)}")
        raise ModelError(f"Błąd połączenia z API: {str(e)}")
        
    except Exception as e:
        logger.error(f"Błąd podczas analizy AI produktu {product['nazwa']}: {str(e)}")
        raise ModelError(str(e))

def analyze_receipt_products(
    products: List[Dict],
    receipt_text: str,
    ollama_url: str,
    model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
) -> List[Dict]:
    """
    Analizuje listę produktów z paragonu.
    
    Args:
        products: Lista słowników z produktami
        receipt_text: Pełny tekst paragonu
        ollama_url: URL API Ollama
        model: Nazwa modelu do użycia
        
    Returns:
        Lista produktów z dodaną analizą AI
    """
    try:
        analyzed_products = []
        
        for product in products:
            try:
                # Walidacja produktu
                validated = _validate_product(product)
                
                # Analiza AI
                ai_analysis = _get_ai_product_analysis(validated, ollama_url, model)
                
                # Połącz dane
                analyzed = {
                    **validated,
                    "standardized_name": ai_analysis["standardized_name"],
                    "category": ai_analysis["category"],
                    "is_frozen": ai_analysis["is_frozen"]
                }
                
                analyzed_products.append(analyzed)
                
            except (ValueError, ModelError) as e:
                logger.error(f"Błąd podczas analizy produktu: {str(e)}")
                analyzed_products.append(product)  # Dodaj oryginalny produkt
                
        return analyzed_products
        
    except Exception as e:
        logger.error(f"Błąd podczas analizy produktów z paragonu: {str(e)}")
        raise

def _validate_and_repair_product(product: Dict) -> Dict:
    """
    Waliduje i naprawia dane produktu.
    
    Args:
        product: Słownik z danymi produktu
        
    Returns:
        Naprawiony słownik z danymi produktu
    """
    try:
        # 1. Sprawdź wymagane pola
        required_fields = ['nazwa', 'ilosc', 'suma']
        missing_fields = [field for field in required_fields if field not in product]
        if missing_fields:
            logger.warning(f"Brak wymaganych pól w produkcie: {', '.join(missing_fields)}")
            raise ValueError(f"Brak wymaganych pól: {', '.join(missing_fields)}")
        
        # 2. Napraw pola numeryczne
        numeric_fields = [
            'ilosc',
            'cena_jednostkowa_przed_rabatem',
            'cena_jednostkowa_po_rabacie',
            'suma'
        ]
        
        for field in numeric_fields:
            if field in product:
                value = product[field]
                if isinstance(value, str):
                    # Usuń znaki specjalne i zamień przecinek na kropkę
                    value = value.replace(' ', '').replace(',', '.')
                    try:
                        product[field] = float(value)
                    except ValueError:
                        logger.warning(f"Nie udało się przekonwertować pola {field} na liczbę: {value}")
                        if field in required_fields:
                            raise ValueError(f"Pole {field} musi być liczbą")
                        else:
                            del product[field]
        
        # 3. Sprawdź i napraw jednostkę miary
        if 'jednostka' not in product:
            # Spróbuj wywnioskować jednostkę z nazwy i ilości
            name_lower = product['nazwa'].lower()
            if any(keyword in name_lower for keyword in ['kg', 'gram', 'g']):
                product['jednostka'] = 'kg'
            elif any(keyword in name_lower for keyword in ['l', 'litr', 'ml']):
                product['jednostka'] = 'l'
            elif any(keyword in name_lower for keyword in ['szt', 'sztuk', 'opak']):
                product['jednostka'] = 'szt'
            else:
                # Domyślnie zakładamy sztuki
                product['jednostka'] = 'szt'
                logger.debug(f"Ustawiono domyślną jednostkę 'szt' dla produktu: {product['nazwa']}")
        
        # 4. Sprawdź i napraw rabaty
        if 'rabat_na_pozycje' in product:
            rabat = product['rabat_na_pozycje']
            if isinstance(rabat, dict):
                if 'kwota' not in rabat or not isinstance(rabat['kwota'], (int, float)):
                    logger.warning(f"Niepoprawny format rabatu dla produktu {product['nazwa']}")
                    del product['rabat_na_pozycje']
            else:
                logger.warning(f"Niepoprawny format rabatu dla produktu {product['nazwa']}")
                del product['rabat_na_pozycje']
        
        # 5. Sprawdź i napraw stawkę VAT
        if 'stawka_vat' in product:
            vat = product['stawka_vat']
            if vat not in ['A', 'B', 'C', 'D']:
                # Spróbuj naprawić
                vat_upper = vat.upper() if isinstance(vat, str) else ''
                if vat_upper in ['A', 'B', 'C', 'D']:
                    product['stawka_vat'] = vat_upper
                else:
                    logger.warning(f"Niepoprawna stawka VAT dla produktu {product['nazwa']}: {vat}")
                    del product['stawka_vat']
        
        # 6. Sprawdź spójność cen
        if all(field in product for field in ['ilosc', 'cena_jednostkowa_po_rabacie', 'suma']):
            expected_sum = round(product['ilosc'] * product['cena_jednostkowa_po_rabacie'], 2)
            actual_sum = round(product['suma'], 2)
            if abs(expected_sum - actual_sum) > 0.01:  # Tolerancja na błędy zaokrągleń
                logger.warning(
                    f"Niespójne ceny dla produktu {product['nazwa']}: "
                    f"oczekiwana suma {expected_sum}, rzeczywista {actual_sum}"
                )
        
        return product
        
    except Exception as e:
        logger.error(f"Błąd podczas walidacji produktu: {str(e)}")
        raise

def analyze_product_item(
    item_data: Dict,
    receipt_text_context: str,
    ollama_url: str,
    model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
) -> Dict:
    """
    Analizuje pojedynczą pozycję z paragonu i wzbogaca ją o dodatkowe informacje.
    
    Args:
        item_data: Słownik z danymi pozycji z paragonu
        receipt_text_context: Kontekst z całego paragonu
        ollama_url: URL do serwera Ollama
        model: Nazwa modelu do użycia
        
    Returns:
        Słownik z wzbogaconymi danymi o produkcie
    """
    try:
        # 1. Waliduj i napraw dane wejściowe
        item_data = _validate_and_repair_product(item_data)
        
        # 2. Standaryzacja nazwy i kategoryzacja przez AI
        ai_analysis = _get_ai_product_analysis(
            item_data,
            ollama_url,
            model
        )
        
        # 3. Określenie czy produkt jest mrożony
        is_frozen = _is_product_frozen(
            item_data['nazwa'],
            ai_analysis.get('standardized_name', ''),
            ai_analysis.get('category', '')
        )
        
        # 4. Obliczenie ceny jednostkowej po rabacie
        unit_price_after_discount = _calculate_unit_price_after_discount(
            item_data.get('unit_price_original', None),
            item_data.get('item_discount_amount', 0),
            item_data.get('item_total_price', 0),
            item_data.get('quantity', 1)
        )
        
        # 5. Wzbogacenie danych o produkcie
        enriched_item = {
            **item_data,  # Zachowaj oryginalne dane
            'item_name_standardized': ai_analysis.get('standardized_name', item_data['nazwa']),
            'ai_category': ai_analysis.get('category', 'INNE'),
            'is_frozen': is_frozen,
            'unit_price_after_discount': unit_price_after_discount
        }
        
        # 6. Końcowa walidacja
        enriched_item = _validate_and_repair_product(enriched_item)
        
        logger.info(f"Pomyślnie przeanalizowano produkt: {item_data['nazwa']}")
        return enriched_item
        
    except Exception as e:
        logger.error(f"Błąd podczas analizy produktu {item_data['nazwa']}: {str(e)}")
        # Zwróć oryginalne dane w przypadku błędu
        return item_data

def _is_product_frozen(
    original_name: str,
    standardized_name: str,
    category: str
) -> bool:
    """
    Określa czy produkt jest mrożony na podstawie nazwy i kategorii.
    """
    # Sprawdź kategorię
    if category == 'MROŻONKI':
        return True
        
    # Sprawdź słowa kluczowe w obu nazwach
    text_to_check = f"{original_name.lower()} {standardized_name.lower()}"
    return any(keyword in text_to_check for keyword in FROZEN_KEYWORDS)

def _calculate_unit_price_after_discount(
    unit_price_original: Optional[float],
    discount_amount: float,
    total_price: float,
    quantity: float
) -> float:
    """
    Oblicza cenę jednostkową po rabacie.
    """
    if unit_price_original is not None:
        # Jeśli mamy oryginalną cenę jednostkową, odejmujemy rabat jednostkowy
        unit_discount = discount_amount / quantity if quantity > 0 else 0
        return unit_price_original - unit_discount
    else:
        # Jeśli nie mamy oryginalnej ceny, dzielimy cenę końcową przez ilość
        return total_price / quantity if quantity > 0 else 0

def _extract_receipt_context(receipt_data: Dict) -> str:
    """
    Wyciąga istotny kontekst z danych paragonu.
    """
    context_parts = []
    
    # Dodaj informacje o sklepie
    if 'sklep' in receipt_data:
        store_data = receipt_data['sklep']
        context_parts.extend([
            store_data.get('nazwa', ''),
            store_data.get('adres', ''),
        ])
    
    # Dodaj datę i godzinę
    context_parts.extend([
        receipt_data.get('data', ''),
        receipt_data.get('godzina', '')
    ])
    
    # Dodaj nazwy wszystkich produktów
    if 'produkty' in receipt_data:
        product_names = [p.get('nazwa', '') for p in receipt_data['produkty']]
        context_parts.extend(product_names)
    
    return ' '.join(filter(None, context_parts)) 