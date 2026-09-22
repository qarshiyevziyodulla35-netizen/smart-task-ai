"""
SmartTask AI - iCalendar (RFC 5545) & Google Calendar Integration Service
Telefon va kompyuter kalendarlariga vazifalarni sinxronizatsiya qilish va
muddati kelganda bildirishnoma (budilnik / eslatma) yuborish xizmati.
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
import urllib.parse


def escape_ical(text: Optional[str]) -> str:
    """RFC 5545 maxsus belgilarni tozalash va formatlash."""
    if not text:
        return ""
    s = str(text).strip()
    s = s.replace("\\", "\\\\")
    s = s.replace(";", "\\;")
    s = s.replace(",", "\\,")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\n", "\\n")
    return s


def build_ical_event(task: Dict[str, Any]) -> str:
    """Bitta vazifa uchun iCalendar VEVENT blokini shakllantiradi."""
    task_id = task.get("id", 0)
    title = escape_ical(task.get("title", "Vazifa"))
    raw_desc = task.get("description", "")
    category = task.get("category", "Ish")
    priority = task.get("priority", "O'rta")
    status = task.get("status", "Yangi")
    due_date = task.get("due_date")
    due_time = (task.get("due_time") or "").strip()
    estimated = task.get("estimated_minutes") or 30

    desc_parts = [
        f"Kategoriya: {category}",
        f"Muhimlik: {priority}",
        f"Status: {status}"
    ]
    if raw_desc:
        desc_parts.append(f"Tavsif: {raw_desc}")
    desc_parts.append("SmartTask AI orqali yaratilgan")
    description = escape_ical("\n".join(desc_parts))

    now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid = f"task-{task_id}-{due_date or 'nodate'}@smarttask.ai"

    # Sana va vaqtni aniqlash
    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_utc}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:{description}",
        f"CATEGORIES:{escape_ical(category)}",
        f"STATUS:{'COMPLETED' if status == 'Bajarildi' else 'CONFIRMED'}"
    ]

    has_time = False
    if due_date:
        try:
            if due_time and len(due_time) >= 4:
                # Soat va daqiqa formatini tekshirish
                time_clean = due_time.replace(".", ":")
                if len(time_clean) == 4 and time_clean[1] == ":":
                    time_clean = "0" + time_clean
                
                dt_str = f"{due_date} {time_clean}"
                start_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                end_dt = start_dt + timedelta(minutes=int(estimated))
                event_lines.append(f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}")
                event_lines.append(f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}")
                has_time = True
            else:
                d = datetime.strptime(due_date, "%Y-%m-%d").date()
                next_d = d + timedelta(days=1)
                event_lines.append(f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}")
                event_lines.append(f"DTEND;VALUE=DATE:{next_d.strftime('%Y%m%d')}")
        except Exception:
            # Agar sana parsingida xato bo'lsa, bugungi sana olinadi
            today = date.today()
            event_lines.append(f"DTSTART;VALUE=DATE:{today.strftime('%Y%m%d')}")
            event_lines.append(f"DTEND;VALUE=DATE:{(today + timedelta(days=1)).strftime('%Y%m%d')}")
    else:
        today = date.today()
        event_lines.append(f"DTSTART;VALUE=DATE:{today.strftime('%Y%m%d')}")
        event_lines.append(f"DTEND;VALUE=DATE:{(today + timedelta(days=1)).strftime('%Y%m%d')}")

    # Telefon qulf ekranida chiqadigan budilnik / eslatma (VALARM)
    alarm_trigger = "-PT15M" if has_time else "-PT0M"
    event_lines.extend([
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Vazifa eslatmasi: {title}",
        f"TRIGGER:{alarm_trigger}",
        "END:VALARM",
        "END:VEVENT"
    ])

    return "\r\n".join(event_lines)


def generate_ical_feed(tasks: List[Dict[str, Any]], calendar_name: str = "SmartTask AI Vazifalari") -> str:
    """Barcha vazifalar uchun to'liq iCalendar (.ics) oqimini yaratadi."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SmartTask AI//UZ",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ical(calendar_name)}",
        "X-WR-TIMEZONE:Asia/Tashkent",
    ]

    for task in tasks:
        # Bajarilganlarni o'tkazib yuborish yoki kiritish (hammasini kiritamiz)
        lines.append(build_ical_event(task))

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def generate_google_calendar_url(task: Dict[str, Any]) -> str:
    """Bitta vazifani Google Calendar-ga 1 bosishda qo'shish uchun havolani yaratadi."""
    title = task.get("title", "SmartTask Vazifasi")
    raw_desc = task.get("description", "")
    category = task.get("category", "Ish")
    priority = task.get("priority", "O'rta")
    due_date = task.get("due_date")
    due_time = (task.get("due_time") or "").strip()
    estimated = task.get("estimated_minutes") or 30

    desc_lines = [
        f"Kategoriya: {category}",
        f"Muhimlik: {priority}",
    ]
    if raw_desc:
        desc_lines.append(f"Tavsif: {raw_desc}")
    desc_lines.append("\nSmartTask AI orqali yuborilgan")
    details = "\n".join(desc_lines)

    # Sana hisoblash
    dates_param = ""
    if due_date:
        try:
            if due_time and len(due_time) >= 4:
                time_clean = due_time.replace(".", ":")
                if len(time_clean) == 4 and time_clean[1] == ":":
                    time_clean = "0" + time_clean
                start_dt = datetime.strptime(f"{due_date} {time_clean}", "%Y-%m-%d %H:%M")
                end_dt = start_dt + timedelta(minutes=int(estimated))
                dates_param = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
            else:
                d = datetime.strptime(due_date, "%Y-%m-%d").date()
                next_d = d + timedelta(days=1)
                dates_param = f"{d.strftime('%Y%m%d')}/{next_d.strftime('%Y%m%d')}"
        except Exception:
            today = date.today()
            dates_param = f"{today.strftime('%Y%m%d')}/{(today + timedelta(days=1)).strftime('%Y%m%d')}"
    else:
        today = date.today()
        dates_param = f"{today.strftime('%Y%m%d')}/{(today + timedelta(days=1)).strftime('%Y%m%d')}"

    params = {
        "action": "TEMPLATE",
        "text": title,
        "details": details,
        "dates": dates_param,
        "ctz": "Asia/Tashkent"
    }
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params)
