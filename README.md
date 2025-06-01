# OCR Manager

OCR Manager to aplikacja do zarządzania finansami osobistymi i spiżarnią, wykorzystująca technologię OCR do automatycznego przetwarzania paragonów. Aplikacja umożliwia śledzenie wydatków, zarządzanie zapasami domowymi oraz planowanie posiłków.

## Funkcje

- **Przetwarzanie Paragonów**
  - Automatyczne wyodrębnianie danych z paragonów
  - Rozpoznawanie produktów, cen i kategorii
  - Możliwość ręcznej edycji i korekty danych

- **Zarządzanie Finansami**
  - Śledzenie wydatków według kategorii
  - Analiza trendów i statystyki
  - Eksport danych do różnych formatów

- **Zarządzanie Spiżarnią**
  - Automatyczne aktualizowanie stanu zapasów
  - Śledzenie produktów mrożonych
  - Powiadomienia o niskim stanie zapasów

- **Planowanie Posiłków**
  - Dodawanie i zarządzanie przepisami
  - Planowanie posiłków w kalendarzu
  - Generowanie list zakupów

## Wymagania Systemowe

- Node.js 18.0 lub nowszy
- npm 9.0 lub nowszy
- Przeglądarka internetowa z obsługą JavaScript

## Instalacja

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/twoje-repo/ocr-manager.git
   cd ocr-manager
   ```

2. Zainstaluj zależności:
   ```bash
   npm install
   ```

3. Skonfiguruj zmienne środowiskowe:
   ```bash
   cp .env.example .env
   ```
   Uzupełnij plik `.env` odpowiednimi wartościami.

4. Uruchom aplikację w trybie deweloperskim:
   ```bash
   npm run dev
   ```

## Struktura Projektu

```
src/
  ├── app/                    # Strony aplikacji
  │   ├── dashboard/         # Strona główna
  │   ├── receipts/         # Zarządzanie paragonami
  │   ├── pantry/           # Zarządzanie spiżarnią
  │   ├── cooking/          # Przepisy i planowanie posiłków
  │   ├── analysis/         # Analiza wydatków
  │   ├── categories/       # Zarządzanie kategoriami
  │   ├── settings/         # Ustawienia aplikacji
  │   └── help/             # Pomoc i FAQ
  ├── components/            # Komponenty React
  │   ├── layout/           # Komponenty układu strony
  │   ├── shared/           # Współdzielone komponenty
  │   └── [feature]/        # Komponenty specyficzne dla funkcji
  ├── lib/                   # Biblioteki i narzędzia
  │   ├── types/            # Definicje TypeScript
  │   ├── utils/            # Funkcje pomocnicze
  │   └── api/              # Integracje z API
  └── styles/               # Style CSS/SCSS
```

## Konfiguracja OCR

Aplikacja wykorzystuje technologię OCR do przetwarzania paragonów. Domyślnie skonfigurowana jest do rozpoznawania polskich paragonów, ale można dostosować ustawienia w panelu administracyjnym:

- Język rozpoznawania: Polski
- Automatyczna poprawa jakości obrazu
- Automatyczne obracanie obrazu
- Próg pewności rozpoznawania: 80%

## Rozwój

1. Utwórz nową gałąź dla swojej funkcji:
   ```bash
   git checkout -b feature/nazwa-funkcji
   ```

2. Wprowadź zmiany i przetestuj:
   ```bash
   npm run test
   ```

3. Wypchnij zmiany:
   ```bash
   git push origin feature/nazwa-funkcji
   ```

## Licencja

Ten projekt jest licencjonowany na warunkach licencji MIT. Szczegółowe informacje znajdują się w pliku [LICENSE](LICENSE).

## Wsparcie

W razie problemów lub pytań:
- Sprawdź sekcję FAQ w aplikacji
- Skontaktuj się z nami: pomoc@ocrmanager.pl
- Godziny wsparcia: Pon-Pt 9:00 - 17:00 