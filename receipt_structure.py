#!/usr/bin/env python3
"""
Moduł analizy strukturalnej paragonów przy użyciu PP-Structure.
"""

import os
import cv2
import numpy as np
from paddleocr import PPStructureV3
from PIL import Image
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import json

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReceiptStructureAnalyzer:
    def __init__(self, 
                 show_log: bool = True,
                 save_folder: str = './output',
                 layout: bool = True,
                 table: bool = True,
                 ocr: bool = True):
        """
        Inicjalizacja analizatora struktury paragonów.
        
        Args:
            show_log: Czy pokazywać logi
            save_folder: Folder na wyniki
            layout: Czy analizować układ
            table: Czy analizować tabele
            ocr: Czy wykonywać OCR
        """
        self.table_engine = PPStructureV3(
            show_log=show_log,
            layout=layout,
            table=table,
            ocr=ocr
        )
        self.save_folder = Path(save_folder)
        self.save_folder.mkdir(parents=True, exist_ok=True)
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Przygotowanie obrazu do analizy.
        
        Args:
            image: Obraz w formacie numpy array
            
        Returns:
            Przetworzony obraz
        """
        # Konwersja do skali szarości
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Normalizacja kontrastu
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        normalized = clahe.apply(gray)
        
        # Redukcja szumu
        denoised = cv2.fastNlMeansDenoising(normalized)
        
        # Binaryzacja adaptacyjna
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            21,
            11
        )
        
        # Konwersja do RGB (wymagane przez PP-Structure)
        rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        
        return rgb
        
    def analyze_receipt(self, 
                       image_path: Union[str, Path],
                       save_visualization: bool = True) -> Dict:
        """
        Analiza struktury paragonu.
        
        Args:
            image_path: Ścieżka do obrazu paragonu
            save_visualization: Czy zapisać wizualizację wyników
            
        Returns:
            Słownik z wynikami analizy
        """
        try:
            # Wczytanie obrazu
            image_path = Path(image_path)
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Nie można wczytać obrazu: {image_path}")
                
            # Przetworzenie obrazu
            processed_img = self.preprocess_image(img)
            
            # Analiza struktury
            result = self.table_engine(processed_img)
            
            # Zapisanie wyników
            result_path = self.save_folder / f"{image_path.stem}_structure.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Wizualizacja wyników
            if save_visualization:
                # Rysowanie wyników na oryginalnym obrazie
                vis_img = processed_img.copy()
                for region in result:
                    if 'bbox' in region:
                        bbox = region['bbox']
                        # Rysowanie prostokąta
                        cv2.rectangle(
                            vis_img,
                            (int(bbox[0]), int(bbox[1])),
                            (int(bbox[2]), int(bbox[3])),
                            (0, 255, 0),
                            2
                        )
                        # Dodanie etykiety
                        if 'type' in region:
                            cv2.putText(
                                vis_img,
                                region['type'],
                                (int(bbox[0]), int(bbox[1] - 10)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (0, 255, 0),
                                2
                            )
                
                # Zapisanie wizualizacji
                vis_path = self.save_folder / f"{image_path.stem}_structure_vis.jpg"
                cv2.imwrite(str(vis_path), vis_img)
            
            # Przetworzenie wyników do bardziej użytecznego formatu
            structured_data = self._process_results(result)
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Błąd podczas analizy paragonu: {str(e)}")
            raise
            
    def _process_results(self, result: List) -> Dict:
        """
        Przetworzenie surowych wyników do struktury danych.
        
        Args:
            result: Lista wyników z PP-Structure
            
        Returns:
            Przetworzone dane w formie słownika
        """
        structured_data = {
            'header': [],
            'items': [],
            'footer': [],
            'tables': []
        }
        
        for region in result:
            # Pominięcie obrazu
            if 'img' in region:
                del region['img']
                
            # Klasyfikacja regionu
            if region.get('type') == 'table':
                structured_data['tables'].append(region)
            elif region.get('type') == 'text':
                # Próba określenia sekcji na podstawie pozycji
                bbox = region.get('bbox', [0, 0, 0, 0])
                y_pos = bbox[1]  # Pozycja y górnej krawędzi
                
                if y_pos < 0.3:  # Górne 30% to nagłówek
                    structured_data['header'].append(region)
                elif y_pos > 0.7:  # Dolne 30% to stopka
                    structured_data['footer'].append(region)
                else:  # Środek to pozycje paragonu
                    structured_data['items'].append(region)
                    
        return structured_data

def main():
    """
    Przykład użycia analizatora.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analiza strukturalna paragonów przy użyciu PP-Structure'
    )
    parser.add_argument(
        'image_path',
        type=str,
        help='Ścieżka do obrazu paragonu'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./output',
        help='Folder na wyniki'
    )
    parser.add_argument(
        '--no-vis',
        action='store_true',
        help='Nie zapisuj wizualizacji'
    )
    
    args = parser.parse_args()
    
    analyzer = ReceiptStructureAnalyzer(save_folder=args.output)
    result = analyzer.analyze_receipt(
        args.image_path,
        save_visualization=not args.no_vis
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main() 