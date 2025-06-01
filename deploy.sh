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
echo "Uruchamianie aplikacji..."
python3 process_receipt.py & # Uruchomienie backendu OCR w tle
npm run dev # Uruchomienie frontendu w trybie deweloperskim

# Aby zatrzymać wszystkie procesy, użyj: pkill -f "python3 process_receipt.py" && pkill -f "npm run dev"

# Konfiguracja Nginx
sudo cp nginx.conf /etc/nginx/sites-available/ocr-manager
sudo ln -sf /etc/nginx/sites-available/ocr-manager /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "Deployment completed!" 