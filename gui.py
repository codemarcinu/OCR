#!/usr/bin/env python3
"""
GUI dla systemu przetwarzania paragonów z OCR i LLM.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import json
from pathlib import Path
import threading
import tempfile
from PIL import Image, ImageTk
import io
import logging
from process_receipt import (
    process_receipt,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_SYSTEM_PROMPT_FILE
)
from database import ReceiptDatabase

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Definicja dostępnych sklepów i ich promptów
STORES = {
    "Lidl": "prompt_lidl.txt",
    "Biedronka": "prompt_biedronka.txt",
    "Kaufland": "prompt_kaufland.txt",
    "Auchan": "prompt_auchan.txt",
    "Inny/Domyślny": DEFAULT_SYSTEM_PROMPT_FILE
}

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
except ImportError as e:
    print(f"Błąd importu: {e}")
    print("Zainstaluj wymagane biblioteki:")
    print("pip install pillow pytesseract pdf2image")
    print("sudo apt-get install tesseract-ocr poppler-utils")
    pytesseract = None
    Image = None

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Biblioteka PyMuPDF (fitz) nie jest zainstalowana.")
    print("Zainstaluj ją używając: pip install PyMuPDF")
    fitz = None

class ReceiptProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesor Paragonów OCR+LLM")
        self.root.geometry("1200x900")  # Zwiększona wysokość okna
        
        # Zmienne
        self.selected_file = tk.StringVar()
        self.model_name = tk.StringVar(value=DEFAULT_OLLAMA_MODEL)
        self.ollama_url = tk.StringVar(value=DEFAULT_OLLAMA_URL)
        self.prompt_file = tk.StringVar(value=DEFAULT_SYSTEM_PROMPT_FILE)
        self.selected_store = tk.StringVar(value="Inny/Domyślny")
        self.preview_image = None
        
        # Inicjalizacja bazy danych
        self.db = ReceiptDatabase()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Główny kontener
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        
        # Sekcja wyboru pliku
        file_frame = ttk.LabelFrame(main_frame, text="Wybór Pliku", padding="5")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Plik:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.selected_file).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(file_frame, text="Wybierz...", command=self.select_file).grid(row=0, column=2)
        
        # Sekcja wyboru sklepu
        store_frame = ttk.LabelFrame(main_frame, text="Wybór Sklepu", padding="5")
        store_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        store_frame.columnconfigure(1, weight=1)
        
        ttk.Label(store_frame, text="Sklep:").grid(row=0, column=0, sticky=tk.W)
        store_combo = ttk.Combobox(store_frame, textvariable=self.selected_store, values=list(STORES.keys()))
        store_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        store_combo.bind('<<ComboboxSelected>>', lambda e: self.update_prompt_file())
        
        # Sekcja podglądu pliku
        preview_frame = ttk.LabelFrame(main_frame, text="Podgląd Pliku", padding="5")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        preview_frame.columnconfigure(0, weight=1)
        
        self.preview_canvas = tk.Canvas(preview_frame, height=250)  # Zwiększona wysokość
        self.preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Sekcja konfiguracji
        config_frame = ttk.LabelFrame(main_frame, text="Konfiguracja", padding="5")
        config_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(config_frame, text="Model:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.model_name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(config_frame, text="URL Ollama:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.ollama_url).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Przycisk przetwarzania
        ttk.Button(main_frame, text="Przetwórz Paragon", command=self.process_receipt).grid(row=4, column=0, pady=5)
        
        # Notebook dla wyników
        self.results_notebook = ttk.Notebook(main_frame)
        self.results_notebook.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Zakładka z tabelą paragonów
        self.receipts_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.receipts_frame, text="Lista Paragonów")
        
        # Tabela paragonów
        self.setup_receipts_table()
        
        # Zakładka z tabelą produktów
        self.products_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.products_frame, text="Lista Produktów")
        
        # Tabela produktów
        self.setup_products_table()
        
        # Zakładka z surowym JSON-em
        self.json_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.json_frame, text="Surowy JSON")
        
        self.json_text = scrolledtext.ScrolledText(self.json_frame, height=15, wrap=tk.WORD)
        self.json_text.pack(fill=tk.BOTH, expand=True)
        
        # Pasek statusu
        self.status_var = tk.StringVar()
        self.status_var.set("Gotowy")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Konfiguracja rozciągania
        main_frame.rowconfigure(5, weight=3)  # Notebook z wynikami
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def setup_receipts_table(self):
        """Konfiguruje tabelę paragonów."""
        columns = ('id', 'data', 'sklep', 'kwota', 'metoda')
        
        self.receipts_tree = ttk.Treeview(self.receipts_frame, columns=columns, show='headings')
        
        # Definiuj nagłówki
        self.receipts_tree.heading('id', text='ID')
        self.receipts_tree.heading('data', text='Data')
        self.receipts_tree.heading('sklep', text='Sklep')
        self.receipts_tree.heading('kwota', text='Kwota')
        self.receipts_tree.heading('metoda', text='Metoda Płatności')
        
        # Definiuj szerokości kolumn
        self.receipts_tree.column('id', width=50)
        self.receipts_tree.column('data', width=100)
        self.receipts_tree.column('sklep', width=100)
        self.receipts_tree.column('kwota', width=100)
        self.receipts_tree.column('metoda', width=150)
        
        # Dodaj scrollbary
        vsb = ttk.Scrollbar(self.receipts_frame, orient="vertical", command=self.receipts_tree.yview)
        hsb = ttk.Scrollbar(self.receipts_frame, orient="horizontal", command=self.receipts_tree.xview)
        self.receipts_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Umieść elementy w gridzie
        self.receipts_tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        # Konfiguruj rozciąganie
        self.receipts_frame.columnconfigure(0, weight=1)
        self.receipts_frame.rowconfigure(0, weight=1)
        
        # Podłącz event kliknięcia
        self.receipts_tree.bind('<<TreeviewSelect>>', self.on_receipt_select)
        
    def setup_products_table(self):
        """Konfiguruje tabelę produktów."""
        columns = ('paragon_id', 'nazwa', 'nazwa_ujednolicona', 'kategoria', 'ilosc', 'jednostka', 'cena_jedn', 'rabat', 'cena_po_rabacie', 'suma', 'czy_mrozony')
        
        self.products_tree = ttk.Treeview(self.products_frame, columns=columns, show='headings')
        
        # Definiuj nagłówki
        self.products_tree.heading('paragon_id', text='ID Paragonu')
        self.products_tree.heading('nazwa', text='Nazwa Oryginalna')
        self.products_tree.heading('nazwa_ujednolicona', text='Nazwa Ujednolicona')
        self.products_tree.heading('kategoria', text='Kategoria')
        self.products_tree.heading('ilosc', text='Ilość')
        self.products_tree.heading('jednostka', text='Jednostka')
        self.products_tree.heading('cena_jedn', text='Cena Jedn.')
        self.products_tree.heading('rabat', text='Rabat')
        self.products_tree.heading('cena_po_rabacie', text='Cena po Rabacie')
        self.products_tree.heading('suma', text='Suma')
        self.products_tree.heading('czy_mrozony', text='Mrożony')
        
        # Definiuj szerokości kolumn
        self.products_tree.column('paragon_id', width=80)
        self.products_tree.column('nazwa', width=200)
        self.products_tree.column('nazwa_ujednolicona', width=200)
        self.products_tree.column('kategoria', width=100)
        self.products_tree.column('ilosc', width=70)
        self.products_tree.column('jednostka', width=70)
        self.products_tree.column('cena_jedn', width=80)
        self.products_tree.column('rabat', width=70)
        self.products_tree.column('cena_po_rabacie', width=100)
        self.products_tree.column('suma', width=80)
        self.products_tree.column('czy_mrozony', width=70)
        
        # Dodaj scrollbary
        vsb = ttk.Scrollbar(self.products_frame, orient="vertical", command=self.products_tree.yview)
        hsb = ttk.Scrollbar(self.products_frame, orient="horizontal", command=self.products_tree.xview)
        self.products_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Umieść elementy w gridzie
        self.products_tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        # Konfiguruj rozciąganie
        self.products_frame.columnconfigure(0, weight=1)
        self.products_frame.rowconfigure(0, weight=1)
        
    def on_receipt_select(self, event):
        """Obsługuje wybór paragonu w tabeli."""
        selection = self.receipts_tree.selection()
        if not selection:
            return
            
        item = self.receipts_tree.item(selection[0])
        receipt_id = item['values'][0]
        
        # Pobierz szczegóły paragonu
        receipt_data = self.db.get_receipt_summary(receipt_id)
        
        # Wyczyść tabelę produktów
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
            
        # Wypełnij tabelę produktów
        for pozycja in receipt_data['pozycje']:
            self.products_tree.insert('', 'end', values=(
                receipt_id,
                pozycja['artykul'],
                pozycja['nazwa_ujednolicona'],
                pozycja['kategoria'],
                pozycja['ilosc'],
                pozycja.get('jednostka', '-'),
                pozycja['cena_jednostkowa'],
                pozycja['rabat'],
                pozycja['cena_po_rabacie'],
                pozycja['cena_total'],
                'Tak' if pozycja['czy_mrozony'] else 'Nie'
            ))
            
    def update_tables(self):
        """Aktualizuje tabele z danymi z bazy."""
        # Wyczyść tabele
        for item in self.receipts_tree.get_children():
            self.receipts_tree.delete(item)
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
            
        # Pobierz i wyświetl paragony
        receipts = self.db.get_all_receipts()
        for receipt in receipts:
            self.receipts_tree.insert('', 'end', values=(
                receipt['id'],
                receipt['data_zakupu'],
                receipt['sklep'],
                f"{receipt['kwota_total']:.2f} zł",
                receipt['metoda_platnosci'] or '-'
            ))
            
    def update_prompt_file(self):
        """Aktualizuje ścieżkę do pliku promptu na podstawie wybranego sklepu."""
        selected_store = self.selected_store.get()
        self.prompt_file.set(STORES[selected_store])
        
    def update_preview(self, file_path: Path):
        """Aktualizuje podgląd pliku."""
        try:
            if file_path.suffix.lower() == '.pdf':
                # Konwertuj pierwszą stronę PDF na obraz
                images = convert_from_path(file_path, first_page=1, last_page=1)
                if images:
                    image = images[0]
                else:
                    raise Exception("Nie udało się wczytać strony PDF")
            else:
                # Wczytaj obraz bezpośrednio
                image = Image.open(file_path)
            
            # Przeskaluj obraz do szerokości canvasu zachowując proporcje
            canvas_width = self.preview_canvas.winfo_width()
            if canvas_width < 100:  # Jeśli canvas jeszcze nie ma wymiarów
                canvas_width = 600  # Zwiększona szerokość
            
            # Maksymalna wysokość podglądu
            max_height = 250  # Zwiększona wysokość
            
            # Oblicz nowe wymiary z zachowaniem proporcji
            ratio = min(canvas_width / image.width, max_height / image.height)
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Aktualizuj canvas
            self.preview_canvas.delete("all")
            self.preview_canvas.config(height=new_height)
            self.preview_image = photo  # Zachowaj referencję
            # Wycentruj obraz w canvas
            x = (canvas_width - new_width) // 2 if canvas_width > new_width else 0
            self.preview_canvas.create_image(x, 0, anchor=tk.NW, image=photo)
            
        except Exception as e:
            print(f"Błąd podczas tworzenia podglądu: {e}")
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                10, 10, anchor=tk.NW,
                text=f"Nie udało się utworzyć podglądu:\n{str(e)}"
            )

    def select_file(self):
        """Wybór pliku paragonu."""
        file_path, _ = filedialog.askopenfilename(
            title='Wybierz paragon',
            filetypes=[
                ('Obrazy', '*.jpg *.jpeg *.png *.bmp'),
                ('PDF', '*.pdf'),
                ('Wszystkie pliki', '*.*')
            ]
        )
        
        if file_path:
            self.selected_file.set(str(file_path))
            self.update_preview(Path(file_path))
            logger.info(f"Wybrano plik: {file_path}")
        else:
            logger.debug("Anulowano wybór pliku")
            
    def process_receipt(self):
        if not self.selected_file.get():
            messagebox.showerror("Błąd", "Wybierz plik do przetworzenia!")
            return
            
        # Uruchom przetwarzanie w osobnym wątku
        self.status_var.set("Przetwarzanie...")
        self.root.update_idletasks()
        
        thread = threading.Thread(target=self._process_receipt_thread)
        thread.daemon = True
        thread.start()
        
    def _process_receipt_thread(self):
        try:
            # Przetwórz paragon
            receipt_data = process_receipt(
                Path(self.selected_file.get()),
                Path(self.prompt_file.get()),
                self.model_name.get(),
                self.ollama_url.get()
            )
            
            # Wyświetl surowy JSON
            formatted_json = json.dumps(receipt_data, indent=2, ensure_ascii=False)
            self.json_text.delete('1.0', tk.END)
            self.json_text.insert('1.0', formatted_json)
            
            # Zapisz do bazy danych
            receipt_id = self.db.save_receipt(receipt_data)
            
            # Zaktualizuj tabele
            self.update_tables()
            
            self.status_var.set(f"Gotowy - Zapisano paragon (ID: {receipt_id})")
            
        except Exception as e:
            error_msg = str(e)
            
            # Sprawdź czy to błąd JSON
            if "JSON" in error_msg:
                detailed_msg = (
                    "Wystąpił błąd podczas przetwarzania odpowiedzi z modelu AI.\n\n"
                    "Możliwe przyczyny:\n"
                    "1. Odpowiedź została przerwana w trakcie generowania\n"
                    "2. Model wygenerował niepoprawną strukturę danych\n"
                    "3. Brakuje wymaganych informacji w odpowiedzi\n\n"
                    f"Szczegóły techniczne:\n{error_msg}"
                )
            # Sprawdź czy to błąd połączenia
            elif "connection" in error_msg.lower() or "ollama" in error_msg.lower():
                detailed_msg = (
                    "Nie można połączyć się z serwerem Ollama.\n\n"
                    "Sprawdź czy:\n"
                    "1. Serwer Ollama jest uruchomiony\n"
                    "2. Adres URL jest poprawny\n"
                    "3. Model jest zainstalowany i dostępny\n\n"
                    f"Szczegóły techniczne:\n{error_msg}"
                )
            # Sprawdź czy to błąd OCR
            elif "OCR" in error_msg or "tekst" in error_msg.lower():
                detailed_msg = (
                    "Nie udało się odczytać tekstu z paragonu.\n\n"
                    "Sprawdź czy:\n"
                    "1. Plik jest czytelny i nie jest uszkodzony\n"
                    "2. Format pliku jest obsługiwany\n"
                    "3. Obraz jest wystarczająco wyraźny\n\n"
                    f"Szczegóły techniczne:\n{error_msg}"
                )
            else:
                detailed_msg = (
                    "Wystąpił nieoczekiwany błąd podczas przetwarzania paragonu.\n\n"
                    f"Szczegóły techniczne:\n{error_msg}"
                )
            
            # Wyświetl błąd w interfejsie
            self.status_var.set("Błąd przetwarzania")
            messagebox.showerror("Błąd przetwarzania", detailed_msg)
            
            # Wyczyść pole JSON i pokaż błąd
            self.json_text.delete('1.0', tk.END)
            self.json_text.insert('1.0', f"BŁĄD PRZETWARZANIA:\n\n{detailed_msg}")
            self.json_text.tag_add("error", "1.0", "end")
            self.json_text.tag_config("error", foreground="red")

def main():
    root = tk.Tk()
    app = ReceiptProcessorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 