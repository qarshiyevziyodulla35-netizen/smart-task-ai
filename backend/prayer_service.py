"""
SmartTask AI - Namoz Vaqtlari Xizmati (Samarqand va O'zbekiston Shaharlari)
Foydalanuvchi joylashuvi (GPS koordinatalari) hamda O'zbekistonning barcha asosiy
shaharlari bo'yicha online namoz vaqtlarini aniqlaydi va kunlik vazifalar doskasiga
avtonom tarzda biriktiradi.
"""

import os
import json
import math
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# O'zbekiston shaharlari koordinatalari bazasi
UZBEKISTAN_CITIES: Dict[str, Dict[str, Any]] = {
    "Samarqand": {"lat": 39.6542, "lon": 66.9597, "name_uz": "Samarqand"},
    "Toshkent": {"lat": 41.2995, "lon": 69.2401, "name_uz": "Toshkent"},
    "Buxoro": {"lat": 39.7681, "lon": 64.4556, "name_uz": "Buxoro"},
    "Andijon": {"lat": 40.7821, "lon": 72.3442, "name_uz": "Andijon"},
    "Namangan": {"lat": 40.9983, "lon": 71.6726, "name_uz": "Namangan"},
    "Farg'ona": {"lat": 40.3842, "lon": 71.7843, "name_uz": "Farg'ona"},
    "Qarshi": {"lat": 38.8606, "lon": 65.7891, "name_uz": "Qarshi"},
    "Termiz": {"lat": 37.2242, "lon": 67.2783, "name_uz": "Termiz"},
    "Xiva": {"lat": 41.3783, "lon": 60.3639, "name_uz": "Xiva"},
    "Urganch": {"lat": 41.5562, "lon": 60.6314, "name_uz": "Urganch"},
    "Nukus": {"lat": 42.4602, "lon": 59.6166, "name_uz": "Nukus"},
    "Navoiy": {"lat": 40.0844, "lon": 65.3792, "name_uz": "Navoiy"},
    "Jizzax": {"lat": 40.1158, "lon": 67.8422, "name_uz": "Jizzax"},
    "Guliston": {"lat": 40.4897, "lon": 68.7842, "name_uz": "Guliston"},
    "Qo'qon": {"lat": 40.5286, "lon": 70.9425, "name_uz": "Qo'qon"}
}

# Standart oylik o'rtacha vaqtlar (Offline zaxira jadvali)
FALLBACK_MONTHLY_TIMINGS = {
    1:  {"Bomdod": "06:15", "Quyosh": "07:45", "Peshin": "12:40", "Asr": "15:30", "Shom": "17:25", "Xufton": "19:00"},
    2:  {"Bomdod": "05:50", "Quyosh": "07:20", "Peshin": "12:45", "Asr": "16:00", "Shom": "18:00", "Xufton": "19:30"},
    3:  {"Bomdod": "05:15", "Quyosh": "06:45", "Peshin": "12:40", "Asr": "16:30", "Shom": "18:35", "Xufton": "20:00"},
    4:  {"Bomdod": "04:30", "Quyosh": "06:00", "Peshin": "12:30", "Asr": "17:00", "Shom": "19:05", "Xufton": "20:40"},
    5:  {"Bomdod": "03:45", "Quyosh": "05:25", "Peshin": "12:25", "Asr": "17:20", "Shom": "19:40", "Xufton": "21:25"},
    6:  {"Bomdod": "03:20", "Quyosh": "05:05", "Peshin": "12:30", "Asr": "17:35", "Shom": "20:00", "Xufton": "21:55"},
    7:  {"Bomdod": "03:35", "Quyosh": "05:15", "Peshin": "12:35", "Asr": "17:35", "Shom": "19:55", "Xufton": "21:45"},
    8:  {"Bomdod": "04:15", "Quyosh": "05:45", "Peshin": "12:35", "Asr": "17:15", "Shom": "19:25", "Xufton": "21:00"},
    9:  {"Bomdod": "04:50", "Quyosh": "06:20", "Peshin": "12:25", "Asr": "16:40", "Shom": "18:35", "Xufton": "20:05"},
    10: {"Bomdod": "05:25", "Quyosh": "06:55", "Peshin": "12:20", "Asr": "15:55", "Shom": "17:45", "Xufton": "19:15"},
    11: {"Bomdod": "05:55", "Quyosh": "07:25", "Peshin": "12:20", "Asr": "15:20", "Shom": "17:10", "Xufton": "18:45"},
    12: {"Bomdod": "06:20", "Quyosh": "07:50", "Peshin": "12:30", "Asr": "15:10", "Shom": "17:05", "Xufton": "18:40"}
}


def find_nearest_city(lat: float, lon: float) -> Tuple[str, float]:
    """Berilgan koordinatalarga eng yaqin O'zbekiston shahrini aniqlaydi."""
    min_dist = float("inf")
    nearest_name = "Samarqand"

    for c_name, c_info in UZBEKISTAN_CITIES.items():
        d_lat = lat - c_info["lat"]
        d_lon = lon - c_info["lon"]
        dist = math.sqrt(d_lat * d_lat + d_lon * d_lon)
        if dist < min_dist:
            min_dist = dist
            nearest_name = c_name

    return nearest_name, min_dist


def fetch_prayer_times_by_location(
    city: Optional[str] = "Samarqand",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Foydalanuvchi tanlagan shahar yoki aniq GPS koordinatalari (lat, lon) bo'yicha
    namoz vaqtlarini AlAdhan API orqali oladi. Tarmoq xatolarida zaxira jadvaldan hisoblaydi.
    """
    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")

    loc_name = city or "Samarqand"
    query_url = None

    if lat is not None and lon is not None:
        # Aniq koordinata orqali so'rov
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        api_date = dt.strftime("%d-%m-%Y")
        query_url = f"https://api.aladhan.com/v1/timings/{api_date}?latitude={lat}&longitude={lon}&method=3"
        nearest_c, _ = find_nearest_city(lat, lon)
        loc_name = f"GPS Joylashuv ({nearest_c})"
    else:
        # Shahar nomi orqali so'rov
        norm_city = city.strip().capitalize() if city else "Samarqand"
        if norm_city in UZBEKISTAN_CITIES:
            c_info = UZBEKISTAN_CITIES[norm_city]
            loc_name = c_info["name_uz"]
            c_lat, c_lon = c_info["lat"], c_info["lon"]
            dt = datetime.strptime(target_date, "%Y-%m-%d")
            api_date = dt.strftime("%d-%m-%Y")
            query_url = f"https://api.aladhan.com/v1/timings/{api_date}?latitude={c_lat}&longitude={c_lon}&method=3"
        else:
            loc_name = norm_city
            dt = datetime.strptime(target_date, "%Y-%m-%d")
            api_date = dt.strftime("%d-%m-%Y")
            query_url = f"https://api.aladhan.com/v1/timingsByCity/{api_date}?city={norm_city}&country=Uzbekistan&method=3"

    timings = None
    if query_url:
        try:
            req = urllib.request.Request(query_url, headers={"User-Agent": "SmartTaskAI/2.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("code") == 200 and "data" in data:
                    raw = data["data"]["timings"]
                    def clean_time(s: str) -> str:
                        return s.split()[0][:5]
                    timings = {
                        "Bomdod": clean_time(raw.get("Fajr", "05:00")),
                        "Quyosh": clean_time(raw.get("Sunrise", "06:30")),
                        "Peshin": clean_time(raw.get("Dhuhr", "12:30")),
                        "Asr": clean_time(raw.get("Asr", "16:15")),
                        "Shom": clean_time(raw.get("Maghrib", "18:20")),
                        "Xufton": clean_time(raw.get("Isha", "19:45"))
                    }
        except Exception as e:
            logger.warning(f"Namoz vaqtlari API so'rovida ogohlantirish: {e}")

    # Agar API javob bermasa, zaxira jadval
    if not timings:
        try:
            m = datetime.strptime(target_date, "%Y-%m-%d").month
        except Exception:
            m = date.today().month
        timings = FALLBACK_MONTHLY_TIMINGS.get(m, FALLBACK_MONTHLY_TIMINGS[10]).copy()

    # Keyingi namoz va qolgan vaqtni hisoblash
    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute

    prayer_order = ["Bomdod", "Peshin", "Asr", "Shom", "Xufton"]
    next_prayer = "Bomdod"
    remaining_mins = 0

    for p in prayer_order:
        t_str = timings.get(p, "00:00")
        try:
            p_h, p_m = map(int, t_str.split(":"))
            p_total = p_h * 60 + p_m
            if p_total > now_minutes:
                next_prayer = p
                remaining_mins = p_total - now_minutes
                break
        except Exception:
            pass
    else:
        # Agar barcha namozlar o'tgan bo'lsa, keyingisi ertangi Bomdod
        next_prayer = "Bomdod (ertaga)"
        try:
            b_h, b_m = map(int, timings.get("Bomdod", "05:00").split(":"))
            remaining_mins = (24 * 60 - now_minutes) + (b_h * 60 + b_m)
        except Exception:
            remaining_mins = 360

    rem_hours = remaining_mins // 60
    rem_sub_mins = remaining_mins % 60
    if rem_hours > 0:
        rem_text = f"{rem_hours} soat {rem_sub_mins} daqiqa"
    else:
        rem_text = f"{rem_sub_mins} daqiqa"

    return {
        "city": loc_name,
        "date": target_date,
        "timings": timings,
        "next_prayer": next_prayer,
        "remaining_minutes": remaining_mins,
        "remaining_text": rem_text,
        "is_online": True
    }


def fetch_samarkand_prayer_times(target_date: Optional[str] = None) -> Dict[str, str]:
    """Mavjud kodlar bilan to'liq orqaga moslik (backward compatibility)."""
    res = fetch_prayer_times_by_location("Samarqand", target_date=target_date)
    return res["timings"]


def auto_schedule_samarkand_prayers(
    target_date: Optional[str] = None,
    city: Optional[str] = "Samarqand",
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Namoz vazifalarini avtonom tarzda bazaga kiritadi va yangilaydi.
    Agar vazifalar allaqachon mavjud bo'lsa, ularning vaqtini yangilaydi.
    """
    from backend import database

    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")

    ensure_prayer_category()

    data = fetch_prayer_times_by_location(city=city, lat=lat, lon=lon, target_date=target_date)
    timings = data["timings"]
    city_name = data["city"]

    existing_tasks = database.list_tasks(date_filter=target_date)
    prayer_tasks_map = {t["title"].strip(): t for t in existing_tasks if t.get("category") == "Ibodat"}

    prayer_info = [
        ("🕌 Bomdod namozi", timings.get("Bomdod", "05:00")),
        ("🕌 Peshin namozi", timings.get("Peshin", "12:30")),
        ("🕌 Asr namozi", timings.get("Asr", "16:00")),
        ("🕌 Shom namozi", timings.get("Shom", "18:20")),
        ("🕌 Xufton namozi", timings.get("Xufton", "19:45")),
    ]

    result_tasks = []
    for title, p_time in prayer_info:
        if title in prayer_tasks_map:
            # Agar mavjud bo'lsa, yangi vaqt bo'yicha yangilash
            cur_task = prayer_tasks_map[title]
            if cur_task.get("due_time") != p_time:
                database.update_task(cur_task["id"], {"due_time": p_time, "description": f"{city_name} bo'yicha namoz vaqti."})
            result_tasks.append(cur_task)
        else:
            task = database.create_task(
                title=title,
                description=f"{city_name} bo'yicha avtonom namoz vaqti va eslatmasi.",
                category="Ibodat",
                priority="Yuqori",
                due_date=target_date,
                due_time=p_time,
                estimated_minutes=25,
                status="Yangi"
            )
            result_tasks.append(task)
            logger.info(f"Namoz vazifasi qo'shildi: {title} ({p_time}) - {city_name}")

    return result_tasks


def ensure_prayer_category():
    """Ibodat kategoriyasini tekshirish va yaratish."""
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
