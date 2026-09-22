import os
import re
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from . import database


def get_gemini_client():
    api_key = database.get_setting("gemini_api_key", os.environ.get("GEMINI_API_KEY", ""))
    if not api_key or not GENAI_AVAILABLE:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def parse_task_nlp(user_text: str) -> Dict[str, Any]:
    """
    Foydalanuvchi tabiiy tilda yozgan matndan vazifa parametrlarini ajratib oladi.
    Masalan: 'Ertaga soat 15:00 da hisobot topshirish kerak, juda muhim ish'
    """
    client = get_gemini_client()
    today_str = date.today().strftime("%Y-%m-%d")
    
    if client:
        try:
            prompt = f"""
            Sen vazifalarni tahlil qiluvchi aqlli yordamchisan. Bugungi sana: {today_str}.
            Foydalanuvchi kiritgan matndan quyidagi JSON formatdagi ma'lumotlarni ajratib ber:
            {{
                "title": "vazifa nomi (qisqa va aniq)",
                "description": "batafsil tavsif yoki bo'sh qoldirilsin",
                "category": "Ish" yoki "Shaxsiy" yoki "O'qish" yoki "Salomatlik" yoki "Boshqa",
                "priority": "Yuqori" yoki "O'rta" yoki "Past",
                "due_date": "YYYY-MM-DD",
                "due_time": "HH:MM" (agar vaqt ko'rsatilmagan bo'lsa bo'sh qoldirilsin),
                "estimated_minutes": 30
            }}
            Foydalanuvchi matni: "{user_text}"
            Faqat to'g'ri JSON qaytar, boshqa hech qanday izoh qo'shma.
            """
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(response.text.strip())
            return parsed
        except Exception:
            pass

    # Fallback: O'zbek tili uchun qoidalar asosidagi aqlli tahlil
    text_lower = user_text.lower()
    
    # Sana aniqlash
    target_date = date.today()
    if "ertaga" in text_lower or "ertangi" in text_lower:
        target_date = date.today() + timedelta(days=1)
    elif "indinga" in text_lower:
        target_date = date.today() + timedelta(days=2)
    elif "dushanba" in text_lower:
        days_ahead = (0 - date.today().weekday()) % 7 or 7
        target_date = date.today() + timedelta(days=days_ahead)
    elif "seshanba" in text_lower:
        days_ahead = (1 - date.today().weekday()) % 7 or 7
        target_date = date.today() + timedelta(days=days_ahead)
    elif "chorshanba" in text_lower:
        days_ahead = (2 - date.today().weekday()) % 7 or 7
        target_date = date.today() + timedelta(days=days_ahead)
    elif "payshanba" in text_lower:
        days_ahead = (3 - date.today().weekday()) % 7 or 7
        target_date = date.today() + timedelta(days=days_ahead)
    elif "juma" in text_lower:
        days_ahead = (4 - date.today().weekday()) % 7 or 7
        target_date = date.today() + timedelta(days=days_ahead)
    elif "shanba" in text_lower:
        days_ahead = (5 - date.today().weekday()) % 7 or 7
        target_date = date.today() + timedelta(days=days_ahead)
    elif "yakshanba" in text_lower:
        days_ahead = (6 - date.today().weekday()) % 7 or 7
        target_date = date.today() + timedelta(days=days_ahead)

    # Aniq sana formati (masalan 2026-09-25 yoki 25.09)
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', user_text)
    if date_match:
        due_date_str = date_match.group(0)
    else:
        due_date_str = target_date.strftime("%Y-%m-%d")

    # Vaqt aniqlash
    time_str = ""
    time_match = re.search(r'(soat\s*)?(\d{1,2})[:.-](\d{2})', text_lower)
    if time_match:
        hour = int(time_match.group(2))
        minute = int(time_match.group(3))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            time_str = f"{hour:02d}:{minute:02d}"
    else:
        hour_match = re.search(r'soat\s*(\d{1,2})(\s*da)?', text_lower)
        if hour_match:
            hour = int(hour_match.group(1))
            if 0 <= hour <= 23:
                time_str = f"{hour:02d}:00"

    # Ustuvorlik (Priority)
    priority = "O'rta"
    if any(w in text_lower for w in ["muhim", "shoshilinch", "tezkor", "yuqori", "urgent", "tezda", "zarur"]):
        priority = "Yuqori"
    elif any(w in text_lower for w in ["oddiy", "past", "muhim emas", "bo'sh vaqtda", "keyinroq"]):
        priority = "Past"

    # Kategoriya (Category)
    category = "Ish"
    if any(w in text_lower for w in ["dars", "o'qish", "kitob", "ingliz", "kurs", "imtihon", "vazifa"]):
        category = "O'qish"
    elif any(w in text_lower for w in ["sport", "mashq", "yugurish", "zal", "suv", "dorilar", "shifokor", "salomatlik"]):
        category = "Salomatlik"
    elif any(w in text_lower for w in ["uy", "oila", "bozor", "shaxsiy", "do'st", "dam", "xarid"]):
        category = "Shaxsiy"

    # Toza sarlavha
    clean_title = user_text
    # Tozalash
    for phrase in ["bugun", "ertaga", "indinga", "soat", "muhim", "shoshilinch", "juda muhim"]:
        clean_title = re.sub(rf'\b{phrase}\b', '', clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip(",.- ")
    if not clean_title or len(clean_title) < 3:
        clean_title = user_text

    return {
        "title": clean_title,
        "description": user_text,
        "category": category,
        "priority": priority,
        "due_date": due_date_str,
        "due_time": time_str,
        "estimated_minutes": 30
    }


def generate_daily_report(target_date: Optional[str] = None) -> Dict[str, Any]:
    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")
        
    stats = database.get_period_stats(target_date, target_date)
    total = stats["total_tasks"]
    completed = stats["completed_tasks"]
    rate = stats["completion_rate"]
    tasks = stats["tasks"]
    
    # Baholash darajasi
    if rate >= 90:
        grade = "A'lo darajada (Mukammal)"
        badge_color = "emerald"
    elif rate >= 75:
        grade = "Yaxshi (Yuqori unumdorlik)"
        badge_color = "blue"
    elif rate >= 50:
        grade = "O'rtacha natija"
        badge_color = "amber"
    else:
        grade = "E'tibor talab qiladi (Past unumdorlik)"
        badge_color = "rose"

    client = get_gemini_client()
    ai_text = ""
    
    if client and total > 0:
        try:
            task_summary_str = "\n".join([
                f"- {t['title']} | Kategoriya: {t['category']} | Ustuvorlik: {t['priority']} | Holat: {t['status']}"
                for t in tasks
            ])
            prompt = f"""
            Siz professional unumdorlik va vaqt boshqaruvi bo'yicha AI murabbiysisiz.
            Foydalanuvchining {target_date} sanasidagi kunlik vazifalarini tahlil qilib, o'zbek tilida ilhomlantiruvchi va aniq amaliy kunlik hisobot yozing.
            
            Statistika:
            Jami vazifalar: {total} ta
            Bajarilgan: {completed} ta
            Bajarilish darajasi: {rate}%
            
            Vazifalar ro'yxati:
            {task_summary_str}
            
            Hisobot formati:
            1. **Kunlik Xulosa va Baho**: Bugungi natijaga xolisona, samimiy baho.
            2. **Asosiy Muvaffaqiyatlar**: Qaysi muhim ishlar uddalandi?
            3. **Bajarilmagan ishlar tahlili**: Nimalar qolib ketdi va nega?
            4. **Ertangi kun uchun 2-3 ta tavsiya**: Ertangi kunni qanday yaxshiroq boshlash kerak.
            5. **Kun iqtibosi**: Motivatsion qisqa fikr.
            """
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            ai_text = res.text
        except Exception:
            pass

    if not ai_text:
        # Offline aqlli hisobot
        completed_titles = [t["title"] for t in tasks if t["status"] == "Bajarildi"]
        pending_tasks = [t for t in tasks if t["status"] != "Bajarildi"]
        high_prio_pending = [t["title"] for t in pending_tasks if t["priority"] == "Yuqori"]

        ai_text = f"""### 📊 {target_date} sanasi uchun Kunlik Tahliliy Hisobot

**1. Kunlik Natija va Baho:**
Bugungi rejalashtirilgan **{total} ta** vazifadan **{completed} tasi ({rate}%)** muvaffaqiyatli yakunlandi.
Kunlik faollik darajasi: **{grade}**.

**2. Asosiy Yutuqlar:**
"""
        if completed_titles:
            for item in completed_titles[:5]:
                ai_text += f"- ✅ {item}\n"
        else:
            ai_text += "- Bugun hali to'liq yakunlangan vazifalar mavjud emas.\n"

        ai_text += "\n**3. E'tibor Qaratish Kerak Bo'lgan Jihatlar:**\n"
        if high_prio_pending:
            ai_text += f"- ⚠️ **Yuqori ustuvorlikdagi qolib ketgan vazifalar**: {', '.join(high_prio_pending)}. Bularni ertangi kun rejasiga birinchi o'ringa qo'yish tavsiya etiladi.\n"
        elif pending_tasks:
            ai_text += f"- Qolgan {len(pending_tasks)} ta vazifani chala qoldirmasdan ertangi kunning birinchi yarmiga taqsimlash maqsadga muvofiq.\n"
        else:
            ai_text += "- Barcha belgilangan vazifalar to'liq bajarilgan, ajoyib intizom!\n"

        ai_text += f"""
**4. Ertangi Kun Uchun Tavsiyalar:**
- Ertangi kunni eng qiyin yoki muhim 1 ta vazifadan boshlang ("Qurbaqani yeng" qoidasi).
- Har 50 daqiqalik intensiv diqqatdan so'ng 10 daqiqa ko'zlarga va tanaga dam bering.
- Kechqurun ertangi kunning 3 ta asosiy maqsadini belgilab oling.

💡 *Fikr: "Katta natijalar har kuni bajariladigan kichik va oddiy qadamlarning yig'indisidir."*
"""

    report_record = database.save_report("daily", target_date, target_date, stats, ai_text)
    return {
        "report_id": report_record["id"],
        "report_type": "daily",
        "date": target_date,
        "grade": grade,
        "badge_color": badge_color,
        "stats": stats,
        "ai_analysis": ai_text
    }


def generate_weekly_report(end_date: Optional[str] = None) -> Dict[str, Any]:
    if not end_date:
        end_date_obj = date.today()
    else:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    start_date_obj = end_date_obj - timedelta(days=6)
    start_date = start_date_obj.strftime("%Y-%m-%d")
    end_date = end_date_obj.strftime("%Y-%m-%d")

    stats = database.get_period_stats(start_date, end_date)
    total = stats["total_tasks"]
    completed = stats["completed_tasks"]
    rate = stats["completion_rate"]
    by_category = stats["by_category"]
    by_priority = stats["by_priority"]
    by_date = stats["by_date"]

    client = get_gemini_client()
    ai_text = ""

    if client and total > 0:
        try:
            prompt = f"""
            Siz unumdorlik tahlilchisisiz. Quyidagi 7 kunlik ({start_date} dan {end_date} gacha) natijalarni tahlil qilib, o'zbek tilida haftalik hisobot yozing.
            
            Haftalik statistika:
            Jami vazifalar: {total} ta
            Bajarilgan: {completed} ta
            Bajarilish ko'rsatkichi: {rate}%
            Kategoriyalar bo'yicha: {json.dumps(by_category, ensure_ascii=False)}
            Ustuvorliklar bo'yicha: {json.dumps(by_priority, ensure_ascii=False)}
            Kunlar kesimi: {json.dumps(by_date, ensure_ascii=False)}
            
            Format:
            1. **Haftaning Bosh Xulosasi**: Unumdorlik sur'ati va asosiy tendensiya.
            2. **Hafta Qahramon Kunlari va Sustliklar**: Eng samarali kun va qaysi kunda vazifalar sustlashgan.
            3. **Sohalar Balansi (Ish / Shaxsiy / O'qish)**: Vaqt to'g'ri taqsimlanganmi?
            4. **Keyingi Hafta Uchun 3 Ta Strategik Qadam**.
            """
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            ai_text = res.text
        except Exception:
            pass

    if not ai_text:
        # Eng samarali kunni aniqlash
        best_day = None
        max_done = -1
        for d, d_stat in by_date.items():
            if d_stat["completed"] > max_done:
                max_done = d_stat["completed"]
                best_day = d

        ai_text = f"""### 📈 {start_date} — {end_date} Haftalik Tahliliy Hisobot

**1. Hafta Xulosasi:**
Ushbu haftada jami **{total} ta** vazifa rejalashtirilib, ulardan **{completed} tasi ({rate}%)** to'liq ado etildi.
Haftalik unumdorlik maromi: **{'Yuqori' if rate >= 70 else 'O\'rtacha' if rate >= 40 else 'Sust'}**.

**2. Samaradorlik Dinamikasi:**
- Eng ko'p vazifa bajarilgan kun: **{best_day or 'Aniqlanmadi'}** ({max_done if max_done > 0 else 0} ta vazifa).
- Haftalik rejadagi kechikkan ishlar soni: **{stats['overdue_tasks']} ta**.

**3. Yo'nalishlar Taqsimoti:**
"""
        for cat, val in by_category.items():
            cat_pct = round((val['completed'] / val['total'] * 100), 1) if val['total'] > 0 else 0
            ai_text += f"- **{cat}**: Jami {val['total']} ta, bajarildi: {val['completed']} ta ({cat_pct}%)\n"

        ai_text += f"""
**4. Keyingi Hafta Uchun Tavsiyalar:**
- Yangi haftaning dushanba kunida haftalik "Top 5" asosiy vazifani belgilang.
- Vazifalarni haddan tashqari ko'p rejalashtirishdan qoching (har kunga 4-6 ta sifatli vazifa kifoya).
- Hafta o'rtasida (chorshanba) qisqa 15 daqiqalik qayta ko'rib chiqish o'tkazing.
"""

    report_record = database.save_report("weekly", start_date, end_date, stats, ai_text)
    return {
        "report_id": report_record["id"],
        "report_type": "weekly",
        "start_date": start_date,
        "end_date": end_date,
        "stats": stats,
        "ai_analysis": ai_text
    }


def generate_monthly_report(year: int, month: int) -> Dict[str, Any]:
    # Oyning boshlanish va tugash sanasi
    start_date = f"{year:04d}-{month:02d}-01"
    if month == 12:
        next_month_date = date(year + 1, 1, 1)
    else:
        next_month_date = date(year, month + 1, 1)
    end_date_obj = next_month_date - timedelta(days=1)
    end_date = end_date_obj.strftime("%Y-%m-%d")

    stats = database.get_period_stats(start_date, end_date)
    total = stats["total_tasks"]
    completed = stats["completed_tasks"]
    rate = stats["completion_rate"]
    by_category = stats["by_category"]

    month_names = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
        7: "Iyul", 8: "Avgust", 9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr"
    }
    month_name = month_names.get(month, str(month))

    client = get_gemini_client()
    ai_text = ""

    if client and total > 0:
        try:
            prompt = f"""
            Siz yuqori darajadagi boshqaruv va shaxsiy rivojlanish bo'yicha ekspertsiz.
            Foydalanuvchining {year}-yil {month_name} oyi bo'yicha natijalarini chuqur tahlil qilib, o'zbek tilida keng qamrovli oylik strategik hisobot tayyorlang.

            Oylik statistika:
            Jami rejalashtirilgan vazifalar: {total} ta
            Muvaffaqiyatli yakunlangan: {completed} ta
            Oylik ko'rsatkich: {rate}%
            Kategoriyalar bo'yicha: {json.dumps(by_category, ensure_ascii=False)}

            Tuzilma:
            1. **Oylik Strategik Xulosa**: Oy yakunlariga baho va erishilgan marralar.
            2. **Odatlar va Intizom Tahlili**: Foydalanuvchining oy davomidagi barqarorligi.
            3. **Kuchli va Zaif Tomonlar**: Qaysi sohada ustunlik va qayerda orqada qolish bor.
            4. **Kelgusi Oy Rejasi Uchun Bosh Tavsiyalar**: 3 ta asosiy yo'nalish.
            """
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            ai_text = res.text
        except Exception:
            pass

    if not ai_text:
        ai_text = f"""### 🏆 {year}-yil {month_name} Oyi Strategik Tahliliy Hisoboti

**1. Oylik Umumiy Ko'rsatkichlar:**
Oy davomida jami **{total} ta** turli xil vazifalar kiritildi. Ulardan **{completed} tasi ({rate}%)** to'liq o'z vaqtida yoki yakuniy holatda bajarildi.
Oylik samaradorlik indeksi: **{rate}%** ({'Ajoyib natija' if rate >= 80 else 'Barqaror o\'sish' if rate >= 50 else 'E\'tiborni oshirish kerak'}).

**2. Sohalar Kesimida Natijadorlik:**
"""
        for cat, val in by_category.items():
            cat_pct = round((val['completed'] / val['total'] * 100), 1) if val['total'] > 0 else 0
            ai_text += f"- **{cat}**: Jami {val['total']} ta | Bajarildi: {val['completed']} ta ({cat_pct}%)\n"

        ai_text += f"""
**3. Oylik Tizimlilik va Xulosalar:**
- Vazifalarning muntazam qayd etilishi shaxsiy intizomni 40% ga oshiradi.
- Oylik maqsadlarni haftalik qismlarga bo'lish qoldirib ketish xavfini kamaytiradi.

**4. Yangi Oy Uchun 3 Ta Bosh Qoida:**
1. Har oy boshida 1 ta ustuvor "Katta Maqsad" (North Star Goal) belgilang.
2. Har haftaning yakunida ushbu oylik maqsadga qanchalik yaqinlashganingizni tekshiring.
3. Kichik g'alabalarni ham nishonlang — bu miyada dofamin ishlab chiqarib, unumdorlikni saqlab qoladi.
"""

    report_record = database.save_report("monthly", start_date, end_date, stats, ai_text)
    return {
        "report_id": report_record["id"],
        "report_type": "monthly",
        "month_name": month_name,
        "year": year,
        "start_date": start_date,
        "end_date": end_date,
        "stats": stats,
        "ai_analysis": ai_text
    }


def chat_coach(message: str, history: List[Dict[str, str]] = None) -> str:
    """
    Foydalanuvchiga unumdorlik, vaqtni to'g'ri taqsimlash va vazifalar bo'yicha maslahat beruvchi AI Coach.
    """
    today_str = date.today().strftime("%Y-%m-%d")
    today_stats = database.get_period_stats(today_str, today_str)
    
    client = get_gemini_client()
    if client:
        try:
            system_instruction = f"""
            Sen "SmartTask AI" platformasining shaxsiy unumdorlik murabbiysi (AI Coach)san.
            Foydalanuvchiga xushmuomala, aniq, ilmiy asoslangan va amaliy tavsiyalar berasan.
            O'zbek tilida gapirasan.
            Bugungi sana: {today_str}.
            Foydalanuvchining bugungi ko'rsatkichlari:
            - Jami vazifalar: {today_stats['total_tasks']}
            - Bajarilgan: {today_stats['completed_tasks']}
            - Foiz: {today_stats['completion_rate']}%
            """
            prompt = f"{system_instruction}\n\nFoydalanuvchi savoli: {message}"
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return res.text
        except Exception:
            pass

    # Offline aqlli javoblar
    msg_l = message.lower()
    if "vaqt" in msg_l or "taqsim" in msg_l or "rejala" in msg_l:
        return (
            "Vaqtni unumli taqsimlash uchun **'Pomodoro'** (25 daqiqa qat'iy diqqat + 5 daqiqa dam) "
            "va **'Eisenhower matritsasi'** (shoshilinch va muhim ishlarni ajratish) usullaridan foydalanishni maslahat beraman. "
            f"Bugungi vazifalaringiz orasida {today_stats['pending_tasks']} ta bajarilishi kutilayotgan vazifa bor. "
            "Ulardan eng muhim 1 tasini hozir tanlab oling va 25 daqiqa chalg'imasdan bajaring!"
        )
    elif "charcha" in msg_l or "motivats" in msg_l or "dangasa" in msg_l or "kayfiyat" in msg_l:
        return (
            "Charchoq his qilish — bu insoniy tabiiy holat. Muhimi o'zingizni ayblamaslik. "
            "Hozir 5-10 daqiqa toza havoga chiqing, suv iching va eng oson, 5 daqiqada hal bo'ladigan bitta kichik vazifani "
            "bajarib tizimda 'Bajarildi' belgisini qo'ying. Bu sizga yangi kuch va ruhiy yengillik beradi!"
        )
    elif "qaysi" in msg_l or "boshla" in msg_l:
        return (
            "Eng ma'qul yondashuv: birinchi navbatda 'Yuqori' ustuvorlikdagi vazifalardan boshlash. "
            "Agar bir nechta bo'lsa, 'Eng ko'p ruhiy yuk berayotgan' vazifani birinchi bo'lib bajaring. "
            "Uni hal qilganingizdan so'ng qolgan barcha ishlar ancha yengil tuyuladi."
        )
    else:
        return (
            f"Salom! Men sizning shaxsiy AI unumdorlik yordamchingizman. "
            f"Bugun sizda jami {today_stats['total_tasks']} ta vazifa rejalashtirilgan bo'lib, "
            f"{today_stats['completed_tasks']} tasi yakunlangan. "
            f"Vazifalar, vaqt boshqaruvi yoki kun tartibi bo'yicha qanday yordam bera olaman?"
        )


def parse_food_nlp(user_text: str) -> Dict[str, Any]:
    """
    Foydalanuvchi yozgan taomnoma matnidan kaloriya, oqsil, uglevod, yog' va taom turini ajratadi.
    Masalan: 'Tushlikda 200gr tovuq filesi, 150gr grechka va sabzavotli salat yedim'
    """
    client = get_gemini_client()
    if client:
        try:
            prompt = f"""
            Siz professional sport dietologi va oziqlanish bo'yicha AI ekspertsiz.
            Foydalanuvchi iste'mol qilgan taom matnidan quyidagi JSON ma'lumotlarni hisoblab bering:
            {{
                "meal_type": "Nonushta" yoki "Tushlik" yoki "Kechki ovqat" yoki "Gazak",
                "food_name": "Umumlashgan qisqa taom nomi",
                "calories": 450.0 (umumiy kaloriya kcal),
                "protein": 45.0 (umumiy oqsil gramm),
                "carbs": 40.0 (umumiy uglevod gramm),
                "fat": 8.0 (umumiy yog' gramm),
                "weight_grams": 350.0 (umumiy taxminiy vazn gramm)
            }}
            Matn: "{user_text}"
            Faqat to'g'ri JSON qaytar, boshqa hech qanday izohsiz.
            """
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(res.text.strip())
            return parsed
        except Exception:
            pass

# O'zbek tili raqamlar lug'ati
UZ_NUMS = {
    "bir": 1, "bitta": 1, "yarim": 0.5, "yarimta": 0.5, "chorak": 0.25,
    "ikki": 2, "ikkita": 2, "uch": 3, "uchta": 3,
    "to'rt": 4, "tort": 4, "to'rtta": 4, "tortta": 4,
    "besh": 5, "beshta": 5, "olti": 6, "oltita": 6,
    "yetti": 7, "yettita": 7, "sakkiz": 8, "sakkizta": 8,
    "to'qqiz": 9, "toqqiz": 9, "to'qqizta": 9,
    "o'n": 10, "on": 10, "o'nta": 10
}

# Mukammal Taomlar va Oziq-ovqatlar Lug'ati (KBJU: 100g va standart porsiya)
FOOD_KNOWLEDGE_BASE = [
    # Ko'p so'zli taomlar (birinchi tekshiriladi)
    {
        "names": ["qovurma lag'mon", "qovurma lagmon"],
        "display": "Qovurma lag'mon",
        "kcal_100": 180, "p_100": 6.5, "c_100": 21.0, "f_100": 7.5,
        "portion_g": 350, "default_unit": "porsiya"
    },
    {
        "names": ["cho'zma lag'mon", "chuzma lagmon", "lag'mon", "lagmon"],
        "display": "Lag'mon",
        "kcal_100": 145, "p_100": 5.5, "c_100": 16.5, "f_100": 6.5,
        "portion_g": 400, "default_unit": "kosa"
    },
    {
        "names": ["qozon kabob", "qozon-kabob", "qozonkabob"],
        "display": "Qozon kabob",
        "kcal_100": 210, "p_100": 13.0, "c_100": 8.0, "f_100": 14.0,
        "portion_g": 350, "default_unit": "porsiya"
    },
    {
        "names": ["tovuq filesi", "tovuq file", "tovuq ko'kragi", "tovuq kokragi", "tovuq go'shti", "tovuq"],
        "display": "Tovuq go'shti (file)",
        "kcal_100": 165, "p_100": 31.0, "c_100": 0.0, "f_100": 3.6,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["tandir somsa", "go'shtli somsa", "somsa", "samsa"],
        "display": "Go'shtli somsa",
        "kcal_100": 240, "p_100": 9.2, "c_100": 23.5, "f_100": 12.5,
        "unit_g": 120, "is_unit": True, "unit_kcal": 290, "unit_p": 11.0, "unit_c": 28.0, "unit_f": 15.0
    },
    {
        "names": ["qovoqli somsa", "qovoq somsa"],
        "display": "Qovoqli somsa",
        "kcal_100": 160, "p_100": 3.5, "c_100": 23.5, "f_100": 6.0,
        "unit_g": 120, "is_unit": True, "unit_kcal": 190, "unit_p": 4.0, "unit_c": 28.0, "unit_f": 7.0
    },
    {
        "names": ["ko'katli somsa", "kukatli somsa"],
        "display": "Ko'katli somsa",
        "kcal_100": 150, "p_100": 4.0, "c_100": 22.0, "f_100": 5.5,
        "unit_g": 120, "is_unit": True, "unit_kcal": 180, "unit_p": 5.0, "unit_c": 26.0, "unit_f": 6.5
    },
    {
        "names": ["to'y oshi", "choyxona oshi", "osh", "palov"],
        "display": "Osh (Palov)",
        "kcal_100": 210, "p_100": 6.0, "c_100": 26.0, "f_100": 9.5,
        "portion_g": 350, "default_unit": "likopcha"
    },
    {
        "names": ["manti"],
        "display": "Manti",
        "kcal_100": 175, "p_100": 7.2, "c_100": 16.5, "f_100": 9.2,
        "unit_g": 90, "is_unit": True, "unit_kcal": 160, "unit_p": 6.5, "unit_c": 15.0, "unit_f": 8.5
    },
    {
        "names": ["sho'rva", "shurva", "sho'rba"],
        "display": "Sho'rva",
        "kcal_100": 90, "p_100": 6.0, "c_100": 4.5, "f_100": 5.5,
        "portion_g": 400, "default_unit": "kosa"
    },
    {
        "names": ["mastava"],
        "display": "Mastava",
        "kcal_100": 85, "p_100": 4.5, "c_100": 9.5, "f_100": 3.3,
        "portion_g": 400, "default_unit": "kosa"
    },
    {
        "names": ["chuchvara"],
        "display": "Chuchvara",
        "kcal_100": 130, "p_100": 5.8, "c_100": 15.0, "f_100": 5.2,
        "portion_g": 350, "default_unit": "kosa"
    },
    {
        "names": ["dimlama"],
        "display": "Dimlama",
        "kcal_100": 95, "p_100": 6.5, "c_100": 5.5, "f_100": 5.0,
        "portion_g": 400, "default_unit": "porsiya"
    },
    {
        "names": ["norin"],
        "display": "Norin",
        "kcal_100": 170, "p_100": 11.2, "c_100": 18.0, "f_100": 5.6,
        "portion_g": 250, "default_unit": "porsiya"
    },
    {
        "names": ["xonim"],
        "display": "Xonim",
        "kcal_100": 160, "p_100": 4.5, "c_100": 24.0, "f_100": 5.5,
        "unit_g": 120, "is_unit": True, "unit_kcal": 190, "unit_p": 5.5, "unit_c": 29.0, "unit_f": 6.5
    },
    {
        "names": ["tovuq shashlik"],
        "display": "Tovuq shashlik",
        "kcal_100": 165, "p_100": 24.0, "c_100": 0.0, "f_100": 7.5,
        "unit_g": 100, "is_unit": True, "unit_kcal": 165, "unit_p": 24.0, "unit_c": 0.0, "unit_f": 7.5
    },
    {
        "names": ["jigar shashlik"],
        "display": "Jigar shashlik",
        "kcal_100": 180, "p_100": 22.0, "c_100": 2.0, "f_100": 9.0,
        "unit_g": 100, "is_unit": True, "unit_kcal": 180, "unit_p": 22.0, "unit_c": 2.0, "unit_f": 9.0
    },
    {
        "names": ["qiyma shashlik", "qo'y shashlik", "shashlik", "kabob"],
        "display": "Shashlik",
        "kcal_100": 220, "p_100": 19.0, "c_100": 1.0, "f_100": 16.0,
        "unit_g": 100, "is_unit": True, "unit_kcal": 220, "unit_p": 19.0, "unit_c": 1.0, "unit_f": 16.0
    },
    {
        "names": ["lavash", "doner", "shaurma"],
        "display": "Lavash",
        "kcal_100": 215, "p_100": 8.7, "c_100": 22.5, "f_100": 10.0,
        "unit_g": 300, "is_unit": True, "unit_kcal": 650, "unit_p": 26.0, "unit_c": 68.0, "unit_f": 30.0
    },
    {
        "names": ["burger", "gamburger", "chizburger"],
        "display": "Burger",
        "kcal_100": 240, "p_100": 11.0, "c_100": 21.0, "f_100": 12.0,
        "unit_g": 200, "is_unit": True, "unit_kcal": 480, "unit_p": 22.0, "unit_c": 42.0, "unit_f": 24.0
    },
    {
        "names": ["xot-dog", "hot-dog", "hotdog"],
        "display": "Xot-dog",
        "kcal_100": 225, "p_100": 8.0, "c_100": 21.5, "f_100": 12.0,
        "unit_g": 150, "is_unit": True, "unit_kcal": 340, "unit_p": 12.0, "unit_c": 32.0, "unit_f": 18.0
    },
    {
        "names": ["pizza", "pitsa"],
        "display": "Pitsa (bo'lak)",
        "kcal_100": 225, "p_100": 9.2, "c_100": 26.5, "f_100": 9.2,
        "unit_g": 120, "is_unit": True, "unit_kcal": 270, "unit_p": 11.0, "unit_c": 32.0, "unit_f": 11.0
    },
    {
        "names": ["kartoshka fri", "fri"],
        "display": "Kartoshka fri",
        "kcal_100": 300, "p_100": 3.4, "c_100": 40.0, "f_100": 14.5,
        "portion_g": 120, "default_unit": "porsiya"
    },
    {
        "names": ["naggets"],
        "display": "Naggets",
        "kcal_100": 280, "p_100": 15.0, "c_100": 16.0, "f_100": 18.0,
        "unit_g": 20, "is_unit": True, "unit_kcal": 48, "unit_p": 3.0, "unit_c": 3.2, "unit_f": 3.6
    },
    {
        "names": ["tuxum", "omlet"],
        "display": "Tuxum",
        "kcal_100": 150, "p_100": 12.6, "c_100": 0.8, "f_100": 10.0,
        "unit_g": 55, "is_unit": True, "unit_kcal": 75, "unit_p": 6.5, "unit_c": 0.5, "unit_f": 5.0
    },
    {
        "names": ["grechka"],
        "display": "Grechka",
        "kcal_100": 115, "p_100": 4.5, "c_100": 23.0, "f_100": 1.3,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["guruch", "oq guruch"],
        "display": "Guruch",
        "kcal_100": 130, "p_100": 2.8, "c_100": 28.0, "f_100": 0.4,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["makaron", "pasta"],
        "display": "Makaron",
        "kcal_100": 140, "p_100": 5.0, "c_100": 28.0, "f_100": 1.0,
        "portion_g": 200, "default_unit": "gr"
    },
    {
        "names": ["ovsyanka", "suli", "suli bo'tqasi"],
        "display": "Ovsyanka (Suli)",
        "kcal_100": 110, "p_100": 4.0, "c_100": 19.0, "f_100": 2.5,
        "portion_g": 200, "default_unit": "kosa"
    },
    {
        "names": ["kartoshka pyure", "pyure"],
        "display": "Kartoshka pyure",
        "kcal_100": 90, "p_100": 2.0, "c_100": 16.0, "f_100": 2.5,
        "portion_g": 200, "default_unit": "gr"
    },
    {
        "names": ["qovurilgan kartoshka"],
        "display": "Qovurilgan kartoshka",
        "kcal_100": 190, "p_100": 2.8, "c_100": 25.0, "f_100": 9.5,
        "portion_g": 200, "default_unit": "gr"
    },
    {
        "names": ["mol go'shti", "mol goshti", "mol go'sht"],
        "display": "Mol go'shti",
        "kcal_100": 215, "p_100": 26.0, "c_100": 0.0, "f_100": 12.5,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["qo'y go'shti", "qoy goshti"],
        "display": "Qo'y go'shti",
        "kcal_100": 260, "p_100": 22.0, "c_100": 0.0, "f_100": 19.0,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["baliq", "baliq go'shti"],
        "display": "Baliq",
        "kcal_100": 135, "p_100": 22.0, "c_100": 0.0, "f_100": 5.0,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["tvorog"],
        "display": "Tvorog",
        "kcal_100": 115, "p_100": 18.0, "c_100": 3.0, "f_100": 3.0,
        "portion_g": 150, "default_unit": "gr"
    },
    {
        "names": ["protein", "gepate", "oqsil kokteyl"],
        "display": "Protein kokteyli",
        "kcal_100": 380, "p_100": 76.0, "c_100": 8.0, "f_100": 4.5,
        "unit_g": 35, "is_unit": True, "unit_kcal": 130, "unit_p": 25.0, "unit_c": 3.0, "unit_f": 1.5
    },
    {
        "names": ["tandir non", "patir", "non"],
        "display": "Non",
        "kcal_100": 250, "p_100": 8.0, "c_100": 50.0, "f_100": 1.5,
        "unit_g": 50, "is_unit": True, "unit_kcal": 125, "unit_p": 4.0, "unit_c": 25.0, "unit_f": 1.0
    },
    {
        "names": ["olma"],
        "display": "Olma",
        "kcal_100": 50, "p_100": 0.4, "c_100": 13.0, "f_100": 0.2,
        "unit_g": 160, "is_unit": True, "unit_kcal": 80, "unit_p": 0.5, "unit_c": 20.0, "unit_f": 0.3
    },
    {
        "names": ["banan"],
        "display": "Banan",
        "kcal_100": 90, "p_100": 1.2, "c_100": 23.0, "f_100": 0.3,
        "unit_g": 120, "is_unit": True, "unit_kcal": 110, "unit_p": 1.4, "unit_c": 28.0, "unit_f": 0.4
    },
    {
        "names": ["achchiq-chuchuk", "shakarob", "achchiq chuchuk", "salat"],
        "display": "Salat (Shakarob)",
        "kcal_100": 30, "p_100": 1.0, "c_100": 4.5, "f_100": 0.5,
        "portion_g": 150, "default_unit": "likopcha"
    },
    {
        "names": ["sut"],
        "display": "Sut",
        "kcal_100": 58, "p_100": 3.2, "c_100": 4.8, "f_100": 3.0,
        "portion_g": 250, "default_unit": "stakan"
    },
    {
        "names": ["qatiq", "kefir"],
        "display": "Qatiq",
        "kcal_100": 52, "p_100": 3.0, "c_100": 4.0, "f_100": 2.5,
        "portion_g": 250, "default_unit": "stakan"
    },
    {
        "names": ["ayron"],
        "display": "Ayron",
        "kcal_100": 36, "p_100": 2.0, "c_100": 2.5, "f_100": 1.8,
        "portion_g": 250, "default_unit": "stakan"
    },
    {
        "names": ["choy"],
        "display": "Choy",
        "kcal_100": 1, "p_100": 0.0, "c_100": 0.2, "f_100": 0.0,
        "portion_g": 200, "default_unit": "piyola"
    },
    {
        "names": ["kofe"],
        "display": "Kofe",
        "kcal_100": 10, "p_100": 0.5, "c_100": 1.5, "f_100": 0.2,
        "portion_g": 200, "default_unit": "finjon"
    },
    {
        "names": ["yong'oq", "yongoq", "bodom"],
        "display": "Yong'oq / Bodom",
        "kcal_100": 650, "p_100": 15.0, "c_100": 14.0, "f_100": 62.0,
        "portion_g": 30, "default_unit": "gr"
    }
]


def parse_food_nlp(user_text: str) -> Dict[str, Any]:
    """
    Foydalanuvchi yozgan taomnoma matnidan kaloriya, oqsil, uglevod, yog' va taom turini ajratadi.
    O'zbek milliy taomlari va porsiyalarini yuqori aniqlikda hisoblaydi.
    """
    # 1. Agar Gemini mavjud bo'lsa, AI orqali hisoblashga harakat qilamiz
    client = get_gemini_client()
    if client:
        try:
            prompt = f"""
            Siz O'zbekiston va xalqaro taomlar, sport dietologiyasi va KBJU (Kaloriya, Oqsil, Uglevod, Yog') bo'yicha professional AI ekspertsiz.
            Foydalanuvchi iste'mol qilgan taom matnidan o'zbek milliy o'lchovlarini (kosa, likopcha, porsiya, dona, bo'lak, gramm, stakan) hisobga olib, quyidagi aniq JSON ma'lumotlarni hisoblab bering:
            {{
                "meal_type": "Nonushta" yoki "Tushlik" yoki "Kechki ovqat" yoki "Gazak",
                "food_name": "Qisqa, chiroyli umumlashtirilgan taom nomi (masalan: Lag'mon va Somsa)",
                "calories": 750.0 (umumiy kaloriya kcal),
                "protein": 35.0 (umumiy oqsil gramm),
                "carbs": 85.0 (umumiy uglevod gramm),
                "fat": 28.0 (umumiy yog' gramm),
                "weight_grams": 500.0 (umumiy taom vazni gramm)
            }}
            Matn: "{user_text}"
            Faqat toza JSON qaytar, boshqa hech qanday so'z yoki izoh yozma.
            """
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw_text = res.text.strip()
            clean_json = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw_text, flags=re.MULTILINE).strip()
            parsed = json.loads(clean_json)
            if parsed.get("calories", 0) > 0:
                return {
                    "meal_type": parsed.get("meal_type", "Tushlik"),
                    "food_name": parsed.get("food_name", user_text[:40]),
                    "calories": round(float(parsed.get("calories", 0)), 1),
                    "protein": round(float(parsed.get("protein", 0)), 1),
                    "carbs": round(float(parsed.get("carbs", 0)), 1),
                    "fat": round(float(parsed.get("fat", 0)), 1),
                    "weight_grams": round(float(parsed.get("weight_grams", 200)), 1)
                }
        except Exception:
            pass

    # 2. Oflayn aqlli KBJU mexanizmi (Ultra-aniq tokenizatsiya va o'zbek o'lchov birliklari)
    text_lower = user_text.lower()
    
    # Taom vaqti (Nonushta, Tushlik, Kechki ovqat, Gazak)
    meal_type = "Tushlik"
    now_hour = datetime.now().hour
    if any(w in text_lower for w in ["nonushta", "ertalab", "tonggi"]):
        meal_type = "Nonushta"
    elif any(w in text_lower for w in ["tushlik", "kunduzi"]):
        meal_type = "Tushlik"
    elif any(w in text_lower for w in ["kechki", "kechqurun", "shom"]):
        meal_type = "Kechki ovqat"
    elif any(w in text_lower for w in ["gazak", "snack", "perekus"]):
        meal_type = "Gazak"
    else:
        if 5 <= now_hour < 11:
            meal_type = "Nonushta"
        elif 11 <= now_hour < 16:
            meal_type = "Tushlik"
        elif 16 <= now_hour < 21:
            meal_type = "Kechki ovqat"
        else:
            meal_type = "Gazak"

    matched_ranges = []
    matched_items = []

    # Taomlarni uzun iboralar bo'yicha saralab qidiramiz
    for item in FOOD_KNOWLEDGE_BASE:
        for name in sorted(item["names"], key=len, reverse=True):
            pattern = rf'(?:\b|^){re.escape(name)}(?:\b|$)'
            m = re.search(pattern, text_lower)
            if m:
                start, end = m.span()
                # Takroriy so'zlar to'qnashuvini oldini olish (masalan 'go'sht' va 'osh')
                overlap = any(s <= start < e or s < end <= e for s, e in matched_ranges)
                if not overlap:
                    matched_ranges.append((start, end))
                    matched_items.append((item, name, start, end))
                    break

    if not matched_items:
        return {
            "meal_type": meal_type,
            "food_name": user_text[:40],
            "calories": 350.0,
            "protein": 20.0,
            "carbs": 40.0,
            "fat": 12.0,
            "weight_grams": 250.0
        }

    total_kcal = 0.0
    total_p = 0.0
    total_c = 0.0
    total_f = 0.0
    total_grams = 0.0
    names_list = []

    for item, name, start, end in matched_items:
        names_list.append(item["display"])

        # Taom atrofidagi matnni aniqlash
        pre = text_lower[max(0, start - 20):start].strip()
        post = text_lower[end:min(len(text_lower), end + 20)].strip()

        # 1. Gramm (200gr, 150g, 100 gramm)
        gram_pre = re.search(r'(\d+)\s*(?:g|gr|gramm|gram)\s*$', pre)
        gram_post = re.search(r'^\s*(\d+)\s*(?:g|gr|gramm|gram)\b', post)
        gram_m = gram_pre or gram_post

        # 2. Kilogramm (1kg, 1.5 kilo)
        kg_pre = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilo)\s*$', pre)
        kg_post = re.search(r'^\s*(\d+(?:\.\d+)?)\s*(?:kg|kilo)\b', post)
        kg_m = kg_pre or kg_post

        # 3. Kosa, likopcha, porsiya, stakan
        portion_pre = re.search(r'(\d+|bir|bitta|ikki|ikkita|uch|uchta|yarim|yarimta)?\s*(kosa|likopcha|tarelka|porsiya|pors|stakan)\s*$', pre)
        portion_post = re.search(r'^\s*(\d+|bir|bitta|ikki|ikkita|uch|uchta|yarim|yarimta)?\s*(kosa|likopcha|tarelka|porsiya|pors|stakan)\b', post)
        portion_m = portion_pre or portion_post

        # 4. Dona, ta, bo'lak, siyx
        unit_pre = re.search(r'(\d+|bir|bitta|ikki|ikkita|uch|uchta|to\'rt|tort|to\'rtta|tortta|besh|beshta|yarim|yarimta|chorak)\s*(?:ta|dona|bo\'lak|bolak|siyx|tilim)?\s*$', pre)
        unit_post = re.search(r'^\s*(\d+|bir|bitta|ikki|ikkita|uch|uchta|to\'rt|tort|to\'rtta|tortta|besh|beshta|yarim|yarimta|chorak)\s*(?:ta|dona|bo\'lak|bolak|siyx|tilim)\b', post)
        unit_m = unit_pre or unit_post

        weight = 0.0
        multiplier = 1.0

        if gram_m:
            weight = float(gram_m.group(1))
            multiplier = weight / 100.0
        elif kg_m:
            weight = float(kg_m.group(1)) * 1000.0
            multiplier = weight / 100.0
        elif portion_m:
            raw_qty = portion_m.group(1) or "1"
            qty = float(UZ_NUMS.get(raw_qty, raw_qty if raw_qty.isdigit() else 1))
            unit_name = portion_m.group(2)
            if unit_name == "kosa":
                weight = qty * 400.0
            elif unit_name in ["likopcha", "tarelka", "porsiya", "pors"]:
                weight = qty * 350.0
            elif unit_name == "stakan":
                weight = qty * 250.0
            else:
                weight = qty * item.get("portion_g", 300)
            multiplier = weight / 100.0
        elif unit_m and (item.get("is_unit") or re.search(r'(?:ta|dona|bo\'lak|bolak|siyx|tilim)', unit_m.group(0))):
            raw_qty = unit_m.group(1)
            qty = float(UZ_NUMS.get(raw_qty, raw_qty if raw_qty.isdigit() else 1))
            if item.get("is_unit"):
                multiplier = qty
                weight = qty * item.get("unit_g", 100)
            else:
                weight = qty * item.get("portion_g", 150)
                multiplier = weight / 100.0
        else:
            if item.get("is_unit"):
                multiplier = 1.0
                weight = item.get("unit_g", 100)
            else:
                weight = item.get("portion_g", 150)
                multiplier = weight / 100.0

        if item.get("is_unit") and not gram_m and not kg_m:
            total_kcal += item["unit_kcal"] * multiplier
            total_p += item["unit_p"] * multiplier
            total_c += item["unit_c"] * multiplier
            total_f += item["unit_f"] * multiplier
        else:
            total_kcal += item["kcal_100"] * multiplier
            total_p += item["p_100"] * multiplier
            total_c += item["c_100"] * multiplier
            total_f += item["f_100"] * multiplier

        total_grams += weight

    return {
        "meal_type": meal_type,
        "food_name": ", ".join(names_list[:3]),
        "calories": round(total_kcal, 1),
        "protein": round(total_p, 1),
        "carbs": round(total_c, 1),
        "fat": round(total_f, 1),
        "weight_grams": round(total_grams, 1)
    }


def estimate_workout_calories(workout_type: str, duration_minutes: int, weight_kg: float = 75.0) -> float:
    """
    MET (Metabolic Equivalent of Task) asosida yoqilgan kaloriyani hisoblaydi:
    Kaloriya = MET * Og'irlik (kg) * Vaqt (soat)
    """
    met_values = {
        "Zal / Kuch mashqlari": 6.0,
        "Yugurish / Kardio": 9.5,
        "Turnik / Brus": 6.5,
        "Suzish": 8.0,
        "Futbol / Basketbol": 7.5,
        "Yurish / Yengil": 3.8,
        "Boshqa": 5.0
    }
    met = met_values.get(workout_type, 5.5)
    hours = duration_minutes / 60.0
    burned = met * weight_kg * hours
    return round(burned, 1)


def parse_workout_nlp(user_text: str, weight_kg: float = 75.0) -> Dict[str, Any]:
    text_lower = user_text.lower()
    
    # Mashq turi
    workout_type = "Zal / Kuch mashqlari"
    if any(w in text_lower for w in ["yugur", "kardio", "yugurish", "yugurdim"]):
        workout_type = "Yugurish / Kardio"
    elif any(w in text_lower for w in ["turnik", "brus", "tortilish"]):
        workout_type = "Turnik / Brus"
    elif any(w in text_lower for w in ["suzish", "basseyn"]):
        workout_type = "Suzish"
    elif any(w in text_lower for w in ["futbol", "to'p", "basketbol"]):
        workout_type = "Futbol / Basketbol"
    elif any(w in text_lower for w in ["yurish", "piyoda"]):
        workout_type = "Yurish / Yengil"

    # Daqiqa aniqlash
    duration = 45
    min_match = re.search(r'(\d+)\s*(daqiqa|minut|min|d)', text_lower)
    hour_match = re.search(r'(\d+)\s*(soat|chas)', text_lower)
    if min_match:
        duration = int(min_match.group(1))
    elif hour_match:
        duration = int(hour_match.group(1)) * 60

    burned = estimate_workout_calories(workout_type, duration, weight_kg)
    return {
        "workout_type": workout_type,
        "duration_minutes": duration,
        "calories_burned": burned,
        "notes": user_text
    }


def generate_fitness_ai_report(date_str: str) -> str:
    summary = database.get_fitness_summary(date_str)
    profile = summary["profile"]
    consumed = summary["consumed_calories"]
    burned = summary["burned_calories"]
    net = summary["net_calories"]
    target = profile["target_calories"]
    protein = summary["total_protein"]
    target_protein = profile["target_protein_g"]
    water = summary["water_ml"]
    target_water = profile["target_water_ml"]

    client = get_gemini_client()
    if client and (consumed > 0 or burned > 0):
        try:
            prompt = f"""
            Siz professional sport shifokori va fitnes murabbiysiz.
            Foydalanuvchining bugungi ko'rsatkichlari:
            - Maqsad: {profile['goal_type']}
            - Kaloriya normasi: {target} kcal
            - Qabul qilingan oziq-ovqat kaloriyasi: {consumed} kcal
            - Mashg'ulotda yoqilgan kaloriya: {burned} kcal
            - Sof kaloriya balansi: {net} kcal
            - Oqsil (Protein): {protein}g / Maqsad: {target_protein}g
            - Ichilgan suv: {water}ml / Maqsad: {target_water}ml
            - Mashg'ulotlar: {len(summary['workouts'])} ta ({summary['total_workout_mins']} daqiqa)

            O'zbek tilida qisqa, professional va ilhomlantiruvchi fitnes xulosasi tayyorlang:
            1. **Kaloriya Balansi Tahlili** (Maqsadga muvofiqmi?)
            2. **Oqsil va Oziqlanish Sifati** (Mushak tiklanishi uchun yetarlimi?)
            3. **Suv va Mashg'ulot Bahosi**
            4. **Ertangi kun uchun 1 ta muhim fitnes tavsiyasi**
            """
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return res.text
        except Exception:
            pass

    # Offline tahlil
    status_text = "optimal me'yorda" if abs(net - target) <= 200 else ("defitsitda (vazn tashlash rejimida)" if net < target else "profilaktik ortiqchalikda (massa yig'ish rejimida)")
    protein_status = "Ajoyib, oqsil normasi to'liq bajarildi!" if protein >= target_protein else f"Oqsil biroz yetishmayapti ({target_protein - protein:.0f}g ko'proq kerak). Tvorog, tuxum yoki tovuq qo'shish tavsiya etiladi."

    return f"""### 🏋️ Fitnes va Kaloriya Kunlik Xulosasi ({date_str})

**1. Kaloriya Balansi:**
- Qabul qilindi: **{consumed} kcal** | Yoqildi (sport): **{burned} kcal**
- Sof balans: **{net} kcal** (Maqsad: {target} kcal). Bugungi holatingiz **{status_text}**.

**2. Makronutrientlar va Oqsil:**
- Oqsil (Protein): **{protein}g / {target_protein}g**. {protein_status}
- Uglevodlar: **{summary['total_carbs']}g** | Yog'lar: **{summary['total_fat']}g**.

**3. Gidratatsiya va Mashg'ulot:**
- Ichilgan suv: **{water} ml** (Kunlik me'yor: {target_water} ml).
- Bugungi mashg'ulotlar davomiyligi: **{summary['total_workout_mins']} daqiqa**.

💡 *Tavsiya: Mashg'ulotdan so'ng 45 daqiqa ichida oqsil va murakkab uglevod iste'mol qilish mushaklar tiklanishi (anabolizm)ni 30% ga tezlashtiradi.*
"""

