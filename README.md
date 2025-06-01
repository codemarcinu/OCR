# Skaner Paragonów

Aplikacja do skanowania i zarządzania paragonami z wykorzystaniem OCR. Projekt składa się z backendu w FastAPI i frontendu w React.

## Wymagania

### Backend
- Python 3.8+
- FastAPI
- Uvicorn
- (inne zależności znajdują się w requirements.txt)

### Frontend
- Node.js 16+
- npm/yarn
- React 18
- TypeScript
- Material-UI

## Instalacja

### Backend

```bash
# Klonowanie repozytorium
git clone [adres-twojego-repo]
cd [nazwa-folderu]

# Utworzenie i aktywacja środowiska wirtualnego
python -m venv venv
source venv/bin/activate  # Linux/macOS
# lub
.\venv\Scripts\activate  # Windows

# Instalacja zależności
pip install -r requirements.txt

# Uruchomienie serwera deweloperskiego
uvicorn app.main:app --reload
```

### Frontend

```bash
# Przejście do katalogu frontend
cd frontend

# Instalacja zależności
npm install

# Uruchomienie serwera deweloperskiego
npm run dev
```

## Struktura projektu

```
.
├── app/                    # Backend (FastAPI)
│   ├── main.py            # Główny plik aplikacji
│   ├── routes/            # Endpointy API
│   ├── models/            # Modele danych
│   └── services/          # Logika biznesowa
│
├── frontend/              # Frontend (React)
│   ├── src/
│   │   ├── components/    # Komponenty React
│   │   ├── pages/        # Strony aplikacji
│   │   └── services/     # Integracja z API
│   └── public/           # Statyczne zasoby
│
└── README.md             # Ten plik
```

## Funkcjonalności

- Logowanie użytkowników
- Dashboard z wykresami i statystykami
- Lista paragonów z wyszukiwaniem
- Szczegóły paragonu z możliwością edycji
- Zarządzanie kategoriami produktów
- Widok stanu magazynowego
- Responsywny interfejs użytkownika

## Licencja

[Twoja licencja] 