#!/bin/bash

# Instalacja zależności Python
echo "Instalacja zależności Python..."
pip install -r requirements.txt

# Instalacja zależności Node.js
echo "Instalacja zależności Node.js..."
npm install

# Budowanie aplikacji Next.js
echo "Budowanie aplikacji Next.js..."
npm run build

# Uruchomienie aplikacji
echo "Uruchamianie frontendu w trybie deweloperskim..."
npm run dev

# Aby uruchomić backend OCR, użyj w osobnym terminalu:
# python3 process_receipt.py <ścieżka_do_paragonu>

# Konfiguracja Nginx
sudo cp nginx.conf /etc/nginx/sites-available/ocr-manager
sudo ln -sf /etc/nginx/sites-available/ocr-manager /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "Deployment completed!" 