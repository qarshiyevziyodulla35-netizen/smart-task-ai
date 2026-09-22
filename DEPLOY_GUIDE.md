# 🚀 SmartTask AI — 24/7 Serverga Deploy Qilish va Ishga Tushirish Qo'llanmasi

Ushbu qo'llanma orqali **SmartTask AI** veb-ilovasi va **Telegram Bot**ini doimiy, 24/7 onlayn ishlaydigan serverga (VPS yoki Docker) o'rnatishingiz mumkin.

---

## 🌟 Tizim Arxitekturasi va Imkoniyatlari

- **Web Server:** FastAPI + Uvicorn (Port 8000).
- **Telegram Bot:** python-telegram-bot (Doimiy fon xizmati, vazifalar eslatmasi, ertalabki reja, kechki hisobot, suv eslatmalari).
- **Kalendar & Eslatmalar:** RFC 5545 `.ics` oqimi va Google Calendar integratsiyasi. Telefon qulf ekranida vazifadan 15 daqiqa oldin budilnik/signal beradi.
- **Ma'lumotlar Bazasi:** SQLite (`/data/smart_task.db`), server qayta ishga tushganda ma'lumotlar saqlanib qoladi (Persistent storage).

---

## 🛠️ VARIANT 1: Docker & Docker Compose Orqali Ishga Tushirish (Eng oson usul)

Agar serveringizda Docker o'rnatilgan bo'lsa, loyihani 1 ta buyruq bilan 24/7 ishga tushirishingiz mumkin:

### 1. Serverga fayllarni yuklash
Loyiha papkasiga o'ting:
```bash
cd /opt/smarttask_ai
```

### 2. `.env` faylini yaratish (ixtiyoriy, tokenlar uchun)
```bash
cat << 'EOF' > .env
TELEGRAM_BOT_TOKEN=8455850980:AAFr7K4LqK6lJvE0a-R6p12Vb1g-m2dM5jU
GEMINI_API_KEY=AIzaSy...sizning_kalitingiz
WEB_APP_URL=https://sizning-domeningiz.uz
EOF
```

### 3. Konteynerni fonga ishga tushirish
```bash
docker compose up -d --build
```

### 4. Holatni tekshirish va loglarni ko'rish
```bash
# Holatni ko'rish
docker compose ps

# Jonli loglarni ko'rish
docker compose logs -f
```

*Qayta yuklanganda yoki server o'chib yonganda Docker konteyner avtomatik ravishda qayta ishga tushadi (`restart: always`).*

---

## 🐧 VARIANT 2: Ubuntu / Debian VPS Serverda 1 Buyruqda O'rnatish

Hetzner, DigitalOcean, AWS, Timeweb yoki har qanday Linux VPS serveringiz bo'lsa:

### 1. Serverga kiring va loyihani yuklang:
```bash
# Server terminalida:
sudo mkdir -p /opt/smarttask_ai
cd /opt/smarttask_ai
# Loyiha fayllarini ushbu papkaga ko'chiring
```

### 2. Avtomatik o'rnatuvchi skriptni ishga tushiring:
```bash
sudo chmod +x deploy/deploy_vps.sh
sudo bash deploy/deploy_vps.sh
```

Ushbu skript:
1. Python3, pip, venv, Nginx va UFW ni o'rnatadi.
2. Kerakli kutubxonalarni o'rnatadi.
3. Systemd servislarini yaratadi va yoqadi (`smarttask-web` va `smarttask-bot`).
4. Nginx orqali 80-portni FastAPI serveriga bog'laydi.
5. Server o'chib-yongan taqdirda ham ilovani avtomatik qayta ishga tushiradi.

### 3. Xizmatlarni boshqarish buyruqlari:
```bash
# Web-server holati
sudo systemctl status smarttask-web

# Telegram bot holati
sudo systemctl status smarttask-bot

# Servislarni qayta ishga tushirish
sudo systemctl restart smarttask-web smarttask-bot

# Jonli loglarni ko'rish
sudo journalctl -u smarttask-bot -f
```

### 4. Bepul HTTPS (SSL) Sertifikat o'rnatish:
Telegram Mini App va brauzer bildirishnomalari ishlashi uchun xavfsiz **HTTPS** kerak.
Agar serveringizga domen ulagan bo'lsangiz (masalan, `task.sizning-sayt.uz`):
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d sizning-domeningiz.uz
```
Certbot avtomatik ravishda Nginx sozlamalarini yangilab, bepul Let's Encrypt SSL o'rnatib beradi.

---

## ☁️ VARIANT 3: Render.com yoki Railway.app (Bulutli platformalar)

Agar shaxsiy VPS bo'lmasa, Render.com da bepul yoki arzon tarifda ishga tushirish mumkin:

1. Loyihani GitHub repozitoriysiga yuklang.
2. **Render.com** da yangi **Web Service** yarating.
3. **Environment:** Docker tanlang.
4. **Environment Variables:**
   - `TELEGRAM_BOT_TOKEN`: Sizning bot tokeningiz
   - `GEMINI_API_KEY`: Google Gemini API kaliti (mavjud bo'lsa)
   - `WEB_APP_URL`: Render bergan `https://smarttask-xxxx.onrender.com` manzili
5. **Disk:** `/app/data` papkasiga 1GB Persistent Disk ulang (baza o'chib ketmasligi uchun).
6. **Deploy** tugmasini bosing.

---

## 📱 Telegram Mini App va Kalendar Integratsiyasini Yakunlash

Serverga o'rnatib, HTTPS domen olganingizdan so'ng:

### 1. Telegram Bot menyusiga WebApp-ni ulash:
1. Saytingizga kiring (`https://sizning-domeningiz.uz`).
2. O'ng yuqoridagi **Sozlamalar (⚙️)** belgisini bosing.
3. **"Veb-sayt xavfsiz https havolasi"** maydoniga domen manzilingizni kiriting: `https://sizning-domeningiz.uz`.
4. **"Sozlamalarni saqlash"** tugmasini bosing.
5. Endi Telegram botingizda pastki chap burchakda **«📱 Ilova»** tugmasi paydo bo'ladi va bot ichida sayt ochiladi!

### 2. Vazifalar Kalendari va Telefon Eslatmalari:
- Saytdagi yuqori paneldagi **📅 Kalendar** belgisini bosing.
- **Obuna havolasini** nusxalab, iPhone (`Sozlamalar > Kalendar > Hisoblar > Obuna qo'shish`) yoki Google Calendar (`Boshqa kalendarlar > Havola orqali qo'shish`) ga kiriting.
- Yoki Telegram botingizga `/kalendar` deb yozing, bot sizga yuklab olish uchun tayyor `.ics` faylni yuboradi.
- **Natija:** Barcha vazifalaringiz telefoningizning asosiy kalendariga tushadi va har bir vazifadan **15 daqiqa oldin** telefoningiz qulf ekranida eslatma chiqaradi!
