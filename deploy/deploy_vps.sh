#!/bin/bash
# ==============================================================================
# SmartTask AI — Ubuntu/Debian VPS Avtomatik O'rnatish Skripti
# Bu skript tizim paketlarini, Python virtual muhitini, Nginx va Systemd
# xizmatlarini avtomatik tarzda sozlaydi va 24/7 rejimda ishga tushiradi.
# ==============================================================================

set -e

echo "=================================================================="
echo "🚀 SmartTask AI — 24/7 VPS O'rnatish Jarayoni Boshlandi"
echo "=================================================================="

# Root ruxsatini tekshirish
if [ "$EUID" -ne 0 ]; then
  echo "❌ Iltimos, skriptni root ruxsati bilan ishga tushiring: sudo bash deploy_vps.sh"
  exit 1
fi

PROJECT_DIR="/opt/smarttask_ai"

# 1. Tizim paketlarini yangilash va o'rnatish
echo "📦 1. Tizim paketlari yangilanmoqda va o'rnatilmoqda..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx curl git ufw

# 2. Loyiha papkasini yaratish
echo "📁 2. Loyiha papkasi tayyorlanmoqda: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/data"

# Agar joriy papkada loyiha fayllari bo'lsa, ularni ko'chirish
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "$SCRIPT_DIR" != "$PROJECT_DIR" ]; then
    echo "📋 Fayllar $PROJECT_DIR ga ko'chirilmoqda..."
    cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR/"
fi

cd "$PROJECT_DIR"

# 3. Python Virtual Muhiti (venv) yaratish va paketlarni o'rnatish
echo "🐍 3. Python virtual muhiti yaratilmoqda..."
python3 -m venv venv
"$PROJECT_DIR/venv/bin/pip" install --upgrade pip
"$PROJECT_DIR/venv/bin/pip" install -r requirements.txt

# 4. Systemd xizmatlarini sozlash
echo "⚙️ 4. Systemd xizmatlari (/etc/systemd/system) sozlanmoqda..."
cp "$PROJECT_DIR/deploy/smarttask-web.service" /etc/systemd/system/
cp "$PROJECT_DIR/deploy/smarttask-bot.service" /etc/systemd/system/

systemctl daemon-reload
systemctl enable smarttask-web.service
systemctl enable smarttask-bot.service
systemctl restart smarttask-web.service
systemctl restart smarttask-bot.service

# 5. Nginx sozlamalari
echo "🌐 5. Nginx veb-serveri sozlanmoqda..."
if [ -f "$PROJECT_DIR/deploy/nginx.conf" ]; then
    cp "$PROJECT_DIR/deploy/nginx.conf" /etc/nginx/sites-available/smarttask
    if [ ! -f /etc/nginx/sites-enabled/smarttask ]; then
        ln -s /etc/nginx/sites-available/smarttask /etc/nginx/sites-enabled/
    fi
    # Default nginx saytini o'chirish
    rm -f /etc/nginx/sites-enabled/default || true
    nginx -t && systemctl reload nginx
fi

# 6. Firewall (UFW)
echo "🛡️ 6. Firewall portlari ochilmoqda..."
ufw allow 'Nginx Full' || true
ufw allow OpenSSH || true

echo "=================================================================="
echo "🎉 O'RNATISH MUVAFFAQIYATLI YAKUNLANDI!"
echo "=================================================================="
echo ""
echo "📊 Xizmatlar holatini tekshirish:"
echo "   systemctl status smarttask-web"
echo "   systemctl status smarttask-bot"
echo ""
echo "📝 Loglarni jonli kuzatish:"
echo "   journalctl -u smarttask-web -f"
echo "   journalctl -u smarttask-bot -f"
echo ""
echo "🔒 Bepul HTTPS (SSL) sertifikat o'rnatish uchun:"
echo "   apt install certbot python3-certbot-nginx -y"
echo "   certbot --nginx -d sizning-domeningiz.uz"
echo ""
echo "Telegram Bot va WebApp endi 24/7 onlayn ishlaydi!"
echo "=================================================================="
