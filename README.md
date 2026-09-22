# 🌟 SmartTask AI: Aqlli Vazifalar Boshqaruvi va AI Hisobotlar Platformasi

SmartTask AI — kunlik vazifalarni samarali rejalashtirish, tabiiy tildagi matnlardan avtomatik vazifa tuzish hamda sun'iy intellekt (AI) yordamida **kunlik**, **haftalik** va **oylik** chuqur tahliliy hisobotlar olish imkonini beruvchi to'liq tizim.

---

## 🚀 Ishga tushirish (Tez va Oson)

Dasturni ishga tushirish uchun quyidagi usullardan birini tanlang:

### 1-usul: Veb-Ilovani ishga tushirish
- `run.bat` fayliga sichqoncha bilan ikki marta bosing. Dastur avtomatik tarzda brauzeringizda ochiladi.

### 2-usul: Telegram Bot & Telegram Mini App (Web App)
1. Telegramda **@BotFather** ga kiring va `/newbot` buyrug'i orqali o'z botingizni oching (bu 30 soniya oladi).
2. BotFather bergan **HTTP API tokenni** nusxalab oling.
3. Saytning yuqori o'ng burchagidagi **Sozlamalar (⚙️)** tugmasini bosib, "Telegram Bot Tokeni" maydoniga qo'ying va "Saqlash" tugmasini bosing. (Shuningdek, u yerdan Telegram Web App URL manzilini ham sozlashingiz mumkin).
4. `run_bot.bat` faylini bosing — botingiz ishga tushadi!
5. Botingizga kiring va `/start` deb yozing:
   - **📱 Ilova** tugmasi orqali to'liq veb-dashboardni Telegramning o'zida **Telegram Mini App** sifatida ochishingiz mumkin!
   - Matnli xabarlar yuborib vazifalar, taomlar va mashqlarni boshqarishingiz mumkin.

---

## 🎯 Asosiy Imkoniyatlar

1. **📱 Telegram Mini App & Bot Integratsiyasi**:
   - Telegramdan chiqmasdan turib chiroyli interfeys orqali barcha vazifalar, grafiklar va hisobotlarni ko'rish.
   - Botga oddiy xabar yuborish: taom, mashq yoki vazifa yozsangiz avtomatik hisoblab saqlaydi.

2. **🏷️ O'zingiz Mustaqil Kategoriyalar Qo'shish**:
   - Istagan paytda yangi kategoriya (masalan: *Dizayn*, *Oila*, *Loyiha*, *Xarid*, *Dasturlash* va hk.) va unga mos belgi (ikonka) tanlab qo'shishingiz mumkin.
   - Barcha yangi kategoriyalar darhol filtrlarda va vazifa qo'shish oynasida paydo bo'ladi. Kerak bo'lmaganlarini osongina o'chirish mumkin.

3. **Tabiiy Tilda Vazifa Yaratish (AI NLP & Ovozli Kiritish 🎙️)**:
   - Istalgan tilda (o'zbekcha) oddiy matn yozing yoki mikrofonga bosib gapiring:
     *Masalan: "Ertaga soat 15:00 da hisobot topshirishim kerak, juda muhim"*
   - AI o'zi avtomatik tarzda vazifa nomi, sanasi, vaqti, ustuvorligi va kategoriyasini aniqlab, rejangizga kiritadi.

4. **Kunlik Vazifalar Doskasi & Pomodoro Fokus Taymeri ⏱️**:
   - Vazifalarni bitta chertish bilan "Bajarildi" holatiga o'tkazish.
   - Kategoriyalar va ustuvorliklar bo'yicha qulay filtrlash.
   - **O'rnatilgan Pomodoro Fokus Taymeri**: Vazifani tanlab, 25 daqiqalik intensiv fokus rejimida ishlash (5 min / 15 min tanaffuslar bilan).

5. **💪 Fitnes & Kaloriya Hisoblash Tizimi (SmartFit & KBJU)**:
   - **AI Oziq-ovqat Tahlilchisi**: *«Tushlikda 200gr tovuq va 150gr grechka yedim»* deb yozing yoki mikrofonda ayting — AI uning kaloriyasi, oqsili (protein), uglevod va yog'larini bir zumda hisoblab kiritadi!
   - **Sof Kaloriya Balansi (Net Calories)**:  
     `Qabul qilingan kaloriya - Sport mashg'ulotida yoqilgan kaloriya = Sof balans`. Maqsadingizga qarab (mushak yig'ish, vazn tashlash yoki saqlash) ko'rsatib boradi.
   - **Makronutrientlar (KBJU)**: Oqsil (Protein), Uglevodlar va Yog'lar balansi diagrammasi.
   - **Gidratatsiya (Suv) Nazorati**: +250ml va +500ml tezkor tugmalar bilan kunlik suv me'yorini kuzatish.
   - **Sport Mashg'ulotlari Kundaligi**: Trenajor zali, yugurish, turnik, suzish va boshqa mashqlarning yoqilgan kaloriyasini ilmiy (MET) formulasida hisoblash.
   - **AI Fitnes Murabbiyi**: Oqsil yetarliligi, kaloriya balansi va tiklanish bo'yicha kunlik tavsiyalar.

6. **📊 Kunlik Hisobot (Daily Report)**:
   - Kunlik unumdorlik darajasi foizda (masalan 85%) va umumiy bahosi ("A'lo", "Yaxshi").
   - Kategoriyalar balansi bo'yicha doiraviy diagramma (Chart.js) va vazifalar taqsimoti.
   - AI tahlili va bir tugma bilan hisobotni chop etish yoki PDF sifatida saqlash.

7. **📈 Haftalik va 🏆 Oylik Strategik Hisobotlar**:
   - 7 kunlik va 30 kunlik ish maromi ustunli diagrammalari.
   - Eng samarali kunlar va AI strategik yo'riqnomasi.

8. **🤖 Shaxsiy AI Murabbiy (Productivity Coach)**:
   - Kun tartibi, vaqtni to'g'ri taqsimlash va motivatsiya bo'yicha interaktiv chat.

9. **Xavfsiz va Mahalliy (Offline-Ready)**:
   - Barcha ma'lumotlar kompyuteringizdagi `data/smart_task.db` SQLite bazasida saqlanadi. Internetsiz ham to'liq ishlaydi.
   - Istasangiz, Sozlamalar bo'limida Google Gemini API kalitini kiritishingiz mumkin.

---

## 📁 Loyiha Tuzilmasi

```
smart_task_ai/
├── backend/
│   ├── database.py       # SQLite ma'lumotlar bazasi va so'rovlar (Vazifalar, Fitnes, Kategoriyalar)
│   ├── ai_agent.py       # AI tahlilchi, NLP parser va hisobotlar
│   └── main.py           # FastAPI server va REST API
├── frontend/
│   ├── index.html        # Zamonaviy veb-dashboard va Telegram Web App interfeysi
│   ├── app.js            # Interaktiv boshqaruv, grafiklar, kategoriyalar va WebApp SDK
│   └── styles.css        # Maxsus stillar va chop etish formati
├── data/
│   └── smart_task.db     # Mahalliy xavfsiz SQLite bazasi
├── telegram_bot.py       # Telegram Bot & Telegram Mini App boshqaruvi
├── run_bot.bat           # Telegram botni tezkor ishga tushirish
├── run_tunnel.bat        # Telegram Mini App uchun HTTPS tunnel (ngrok)
├── start.py              # Portni tekshirib, server va brauzerni ochuvchi skript
├── run.bat               # Veb-ilovasi uchun tezkor ishga tushirish fayli
├── test_system.py        # Tizimni to'liq tekshiruvchi 10 ta avtotest
└── README.md             # Qo'llanma
```
