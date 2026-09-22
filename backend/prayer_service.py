"""
SmartTask AI - Namoz Vaqtlari Xizmati (Samarqand)
Samarqand shahri (39.6542° N, 66.9597° E) uchun 5 vaqt namoz vaqtlarini
AlAdhan API hamda avtonom astronomik hisob-kitoblar orqali aniqlaydi va
har kuni avtomatik ravishda kunlik vazifalar (tasklar) ro'yxatiga kiritadi.
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# Samarqand koordinatalari
SAMARKAND_LAT = 39.6542
SAMARKAND_LON = 66.9597
TIMEZONE = "Asia/Tashkent"

# Standart oylik o'rtacha vaqtlar (Offline zaxira jadvali)
FALLBACK_MONTHLY_TIMINGS = {
    1:  {"Bomdod": "06:15", "Peshin": "12:40", "Asr": "15:30", "Shom": "17:25", "Xufton": "19:00"},
    2:  {"Bomdod": "05:50", "Peshin": "12:45", "Asr": "16:00", "Shom": "18:00", "Xufton": "19:30"},
    3:  {"Bomdod": "05:15", "Peshin": "12:40", "Asr": "16:30", "Shom": "18:35", "Xufton": "20:00"},
    4:  {"Bomdod": "04:30", "Peshin": "12:30", "Asr": "17:00", "Shom": "19:05", "Xufton": "20:40"},
    5:  {"Bomdod": "03:45", "Peshin": "12:25", "Asr": "17:20", "Shom": "19:40", "Xufton": "21:25"},
    6:  {"Bomdod": "03:20", "Peshin": "12:30", "Asr": "17:35", "Shom": "20:00", "Xufton": "21:55"},
    7:  {"Bomdod": "03:35", "Peshin": "12:35", "Asr": "17:35", "Shom": "19:55", "Xufton": "21:45"},
    8:  {"Bomdod": "04:15", "Peshin": "12:35", "Asr": "17:15", "Shom": "19:25", "Xufton": "21:00"},
    9:  {"Bomdod": "04:50", "Peshin": "12:25", "Asr": "16:40", "Shom": "18:35", "Xufton": "20:05"},
    10: {"Bomdod": "05:25", "Peshin": "12:20", "Asr": "15:55", "Shom": "17:45", "Xufton": "19:15"},
    11: {"Bomdod": "05:55", "Peshin": "12:20", "Asr": "15:20", "Shom": "17:10", "Xufton": "18:45"},
    12: {"Bomdod": "06:20", "Peshin": "12:30", "Asr": "15:10", "Shom": "17:05", "Xufton": "18:40"}
}


def fetch_samarkand_prayer_times(target_date: Optional[str] = None) -> Dict[str, str]:
    """
    Samarqand shahri uchun 5 vaqt namoz vaqtini oladi.
    1. AlAdhan API orqali so'raydi.
    2. Tarmoqda uzilish bo'lsa, zaxira astronomik oylik jadvaldan foydalanadi.
    """
    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")

    # API so'rovi
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        api_date = dt.strftime("%d-%m-%Y")
        url = f"https://api.aladhan.com/v1/timingsByCity/{api_date}?city=Samarkand&country=Uzbekistan&method=3"
        req = urllib.request.Request(url, headers={"User-Agent": "SmartTaskAI/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 200 and "data" in data:
                timings = data["data"]["timings"]
                # Faqat soat va daqiqani ajratish (HH:MM)
                def clean_time(t_str: str) -> str:
                    return t_str.split()[0][:5]

                return {
                    "Bomdod": clean_time(timings.get("Fajr", "04:50")),
                    "Peshin": clean_time(timings.get("Dhuhr", "12:25")),
                    "Asr": clean_time(timings.get("Asr", "15:55")),
                    "Shom": clean_time(timings.get("Maghrib", "18:30")),
                    "Xufton": clean_time(timings.get("Isha", "19:55"))
                }
    except Exception as e:
        logger.warning(f"AlAdhan API xatosi ({e}), zaxira jadvaldan olinmoqda...")

    # Zaxira jadvaldan olish
    try:
        month = datetime.strptime(target_date, "%Y-%m-%d").month
    except Exception:
        month = date.today().month

    return FALLBACK_MONTHLY_TIMINGS.get(month, FALLBACK_MONTHLY_TIMINGS[9])


def auto_schedule_samarkand_prayers(target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Samarqand uchun 5 vaqt namoz vazifalarini avtomatik tarzda bazaga kiritadi.
    Agar ushbu kunga allaqachon kiritilgan bo'lsa, qayta dublikat qilmaydi.
    """
    from backend import database

    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")

    # 1. Ibodat kategoriyasi borligiga ishonch hosil qilish
    ensure_prayer_category()

    # 2. Bugungi kunga allaqachon kiritilgan namozlarni tekshirish
    existing_tasks = database.list_tasks(date_filter=target_date)
    existing_titles = {t["title"].strip() for t in existing_tasks if t.get("category") == "Ibodat"}

    timings = fetch_samarkand_prayer_times(target_date)
    created_tasks = []

    prayer_info = [
        ("🕌 Bomdod namozi", timings.get("Bomdod", "04:50")),
        ("🕌 Peshin namozi", timings.get("Peshin", "12:25")),
        ("🕌 Asr namozi", timings.get("Asr", "15:55")),
        ("🕌 Shom namozi", timings.get("Shom", "18:30")),
        ("🕌 Xufton namozi", timings.get("Xufton", "19:55")),
    ]

    for title, p_time in prayer_info:
        if title not in existing_titles:
            task = database.create_task(
                title=title,
                description="Samarqand shahri uchun avtonom namoz vaqti va eslatmasi.",
                category="Ibodat",
                priority="Yuqori",
                due_date=target_date,
                due_time=p_time,
                estimated_minutes=25,
                status="Yangi"
            )
            created_tasks.append(task)
            logger.info(f"Yangi namoz vazifasi qo'shildi: {title} ({p_time})")

    return created_tasks


def ensure_prayer_category():
    """Ibodat kategoriyasi mavjud bo'lmasa, uni bazaga qo'shadi."""
    from backend import database
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = 'Ibodat'")
    if not cursor.fetchone():
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO categories (name, icon, color, created_at) VALUES (?, ?, ?, ?)",
            ("Ibodat", "moon", "emerald", now_str)
        )
        conn.commit()
    conn.close()
