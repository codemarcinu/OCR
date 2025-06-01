#!/bin/bash

# Instalacja zależności
npm install

# Budowanie aplikacji
npm run build

# Instalacja PM2 (jeśli nie jest zainstalowany)
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2
fi

# Uruchomienie aplikacji przez PM2
pm2 delete ocr-manager || true
pm2 start npm --name "ocr-manager" -- start

# Konfiguracja Nginx
sudo cp nginx.conf /etc/nginx/sites-available/ocr-manager
sudo ln -sf /etc/nginx/sites-available/ocr-manager /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "Deployment completed!" 