#!/usr/bin/env python3
"""
Moduł obsługi bazy danych dla aplikacji OCR paragonów
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReceiptDatabase:
    def __init__(self, db_path: Union[str, Path] = 'receipts.db'):
        """
        Inicjalizuje połączenie z bazą danych.
        
        Args:
            db_path: Ścieżka do pliku bazy danych
        """
        self.db_path = Path(db_path)
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """
        Inicjalizuje bazę danych i tworzy tabele jeśli nie istnieją.
        """
        try:
            # Wczytaj schemat bazy danych
            schema_path = Path('database_schema.sql')
            if not schema_path.exists():
                raise FileNotFoundError(f"Nie znaleziono pliku schematu bazy danych: {schema_path}")
            
            schema_sql = schema_path.read_text(encoding='utf-8')
            
            # Utwórz połączenie i wykonaj schemat
            self.conn = sqlite3.connect(self.db_path)
            self.conn.executescript(schema_sql)
            self.conn.commit()
            
            logger.info(f"Pomyślnie zainicjalizowano bazę danych: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Błąd podczas inicjalizacji bazy danych: {str(e)}")
            raise
    
    def close(self):
        """
        Zamyka połączenie z bazą danych.
        """
        if self.conn:
            self.conn.close()
            logger.info("Zamknięto połączenie z bazą danych")
    
    def save_receipt_data(self, receipt_data: Dict) -> int:
        """
        Zapisuje dane paragonu do bazy danych.
        
        Args:
            receipt_data: Słownik z danymi paragonu
            
        Returns:
            ID zapisanego paragonu
        """
        try:
            cursor = self.conn.cursor()
            
            # 1. Zapisz podstawowe dane paragonu
            store_data = receipt_data.get('sklep', {})
            receipt_sql = """
                INSERT INTO receipts (
                    store_name, store_address, store_nip,
                    purchase_date, purchase_time, total_amount,
                    payment_method, receipt_number, register_number,
                    loyalty_card_used, loyalty_card_savings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Przygotuj dane paragonu
            receipt_values = (
                store_data.get('nazwa'),
                store_data.get('adres_sklepu') or store_data.get('adres'),
                store_data.get('nip'),
                receipt_data.get('data'),
                receipt_data.get('godzina'),
                receipt_data.get('platnosc', {}).get('suma'),
                receipt_data.get('platnosc', {}).get('metoda'),
                receipt_data.get('nr_paragonu'),
                receipt_data.get('nr_kasy'),
                bool(receipt_data.get('karta_lidl_plus', {}).get('uzyta', False)),
                receipt_data.get('karta_lidl_plus', {}).get('zaoszczedzono', 0.0)
            )
            
            cursor.execute(receipt_sql, receipt_values)
            receipt_id = cursor.lastrowid
            
            # 2. Zapisz pozycje paragonu
            for item in receipt_data.get('produkty', []):
                item_sql = """
                    INSERT INTO items (
                        receipt_id, item_name, item_name_standardized,
                        quantity, unit, unit_price_original,
                        unit_price_after_discount, item_discount_amount,
                        item_total_price, vat_rate, ai_category,
                        is_frozen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                item_values = (
                    receipt_id,
                    item.get('nazwa'),
                    item.get('item_name_standardized'),
                    item.get('ilosc'),
                    item.get('jednostka'),
                    item.get('cena_jednostkowa_przed_rabatem'),
                    item.get('unit_price_after_discount'),
                    item.get('rabat_na_pozycje', {}).get('kwota'),
                    item.get('suma'),
                    item.get('stawka_vat'),
                    item.get('ai_category'),
                    item.get('is_frozen', False)
                )
                
                cursor.execute(item_sql, item_values)
            
            # 3. Zapisz rabaty ogólne
            for discount in receipt_data.get('rabaty', []):
                discount_sql = """
                    INSERT INTO discounts (
                        receipt_id, discount_name, discount_amount
                    ) VALUES (?, ?, ?)
                """
                
                discount_values = (
                    receipt_id,
                    discount.get('nazwa'),
                    discount.get('wartosc')
                )
                
                cursor.execute(discount_sql, discount_values)
            
            # 4. Zapisz podsumowanie VAT
            for vat in receipt_data.get('platnosc', {}).get('vat', []):
                vat_sql = """
                    INSERT INTO vat_summary (
                        receipt_id, vat_rate, base_amount,
                        vat_amount, vat_percent
                    ) VALUES (?, ?, ?, ?, ?)
                """
                
                # Konwertuj stawkę VAT na wartość procentową
                vat_percent = {
                    'A': 23,
                    'B': 8,
                    'C': 5,
                    'D': 0
                }.get(vat.get('stawka'), 0)
                
                vat_values = (
                    receipt_id,
                    vat.get('stawka'),
                    vat.get('podstawa'),
                    vat.get('kwota'),
                    vat_percent
                )
                
                cursor.execute(vat_sql, vat_values)
            
            # 5. Zapisz wykorzystane kupony
            for coupon in receipt_data.get('karta_lidl_plus', {}).get('wykorzystane_kupony', []):
                coupon_sql = """
                    INSERT INTO used_coupons (
                        receipt_id, coupon_name, coupon_value
                    ) VALUES (?, ?, ?)
                """
                
                coupon_values = (
                    receipt_id,
                    coupon.get('nazwa'),
                    coupon.get('wartosc')
                )
                
                cursor.execute(coupon_sql, coupon_values)
            
            self.conn.commit()
            logger.info(f"Pomyślnie zapisano paragon (ID: {receipt_id})")
            return receipt_id
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Błąd podczas zapisywania paragonu: {str(e)}")
            raise
    
    def get_receipt_by_id(self, receipt_id: int) -> Optional[Dict]:
        """
        Pobiera dane paragonu o podanym ID.
        
        Args:
            receipt_id: ID paragonu
            
        Returns:
            Słownik z danymi paragonu lub None jeśli nie znaleziono
        """
        try:
            cursor = self.conn.cursor()
            
            # 1. Pobierz podstawowe dane paragonu
            receipt_sql = """
                SELECT * FROM receipts WHERE receipt_id = ?
            """
            cursor.execute(receipt_sql, (receipt_id,))
            receipt_row = cursor.fetchone()
            
            if not receipt_row:
                return None
            
            # Konwertuj krotkę na słownik
            receipt_data = dict(zip([col[0] for col in cursor.description], receipt_row))
            
            # 2. Pobierz pozycje paragonu
            items_sql = """
                SELECT * FROM items WHERE receipt_id = ?
            """
            cursor.execute(items_sql, (receipt_id,))
            items = [dict(zip([col[0] for col in cursor.description], row))
                    for row in cursor.fetchall()]
            receipt_data['items'] = items
            
            # 3. Pobierz rabaty
            discounts_sql = """
                SELECT * FROM discounts WHERE receipt_id = ?
            """
            cursor.execute(discounts_sql, (receipt_id,))
            discounts = [dict(zip([col[0] for col in cursor.description], row))
                        for row in cursor.fetchall()]
            receipt_data['discounts'] = discounts
            
            # 4. Pobierz podsumowanie VAT
            vat_sql = """
                SELECT * FROM vat_summary WHERE receipt_id = ?
            """
            cursor.execute(vat_sql, (receipt_id,))
            vat_summary = [dict(zip([col[0] for col in cursor.description], row))
                          for row in cursor.fetchall()]
            receipt_data['vat_summary'] = vat_summary
            
            # 5. Pobierz wykorzystane kupony
            coupons_sql = """
                SELECT * FROM used_coupons WHERE receipt_id = ?
            """
            cursor.execute(coupons_sql, (receipt_id,))
            coupons = [dict(zip([col[0] for col in cursor.description], row))
                      for row in cursor.fetchall()]
            receipt_data['used_coupons'] = coupons
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania paragonu {receipt_id}: {str(e)}")
            return None
    
    def get_receipts_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        store_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Pobiera paragony z zadanego zakresu dat.
        
        Args:
            start_date: Data początkowa
            end_date: Data końcowa
            store_name: Opcjonalna nazwa sklepu do filtrowania
            
        Returns:
            Lista słowników z danymi paragonów
        """
        try:
            cursor = self.conn.cursor()
            
            # Przygotuj zapytanie SQL
            sql = """
                SELECT receipt_id FROM receipts
                WHERE purchase_date BETWEEN ? AND ?
            """
            params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
            
            if store_name:
                sql += " AND store_name = ?"
                params.append(store_name)
            
            cursor.execute(sql, params)
            receipt_ids = [row[0] for row in cursor.fetchall()]
            
            # Pobierz pełne dane dla każdego paragonu
            receipts = []
            for receipt_id in receipt_ids:
                receipt_data = self.get_receipt_by_id(receipt_id)
                if receipt_data:
                    receipts.append(receipt_data)
            
            return receipts
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania paragonów: {str(e)}")
            return []
    
    def get_product_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> Dict:
        """
        Generuje statystyki produktów.
        
        Args:
            start_date: Opcjonalna data początkowa
            end_date: Opcjonalna data końcowa
            category: Opcjonalna kategoria do filtrowania
            
        Returns:
            Słownik ze statystykami
        """
        try:
            cursor = self.conn.cursor()
            
            # Przygotuj warunki WHERE
            conditions = []
            params = []
            
            if start_date:
                conditions.append("r.purchase_date >= ?")
                params.append(start_date.strftime('%Y-%m-%d'))
            
            if end_date:
                conditions.append("r.purchase_date <= ?")
                params.append(end_date.strftime('%Y-%m-%d'))
            
            if category:
                conditions.append("i.ai_category = ?")
                params.append(category)
            
            where_clause = " AND ".join(conditions)
            if where_clause:
                where_clause = "WHERE " + where_clause
            
            # Pobierz statystyki
            stats_sql = f"""
                SELECT 
                    i.ai_category,
                    COUNT(DISTINCT i.item_id) as unique_products,
                    COUNT(i.item_id) as total_occurrences,
                    SUM(i.item_total_price) as total_spent,
                    AVG(i.unit_price_after_discount) as avg_unit_price,
                    SUM(i.item_discount_amount) as total_discounts
                FROM items i
                JOIN receipts r ON i.receipt_id = r.receipt_id
                {where_clause}
                GROUP BY i.ai_category
            """
            
            cursor.execute(stats_sql, params)
            stats = {}
            
            for row in cursor.fetchall():
                category_name = row[0] or 'INNE'
                stats[category_name] = {
                    'unique_products': row[1],
                    'total_occurrences': row[2],
                    'total_spent': row[3],
                    'avg_unit_price': row[4],
                    'total_discounts': row[5]
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania statystyk: {str(e)}")
            return {} 