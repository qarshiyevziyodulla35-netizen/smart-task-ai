import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "smart_task.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        category TEXT DEFAULT 'Ish',
        priority TEXT DEFAULT 'O''rta',
        status TEXT DEFAULT 'Yangi',
        due_date TEXT NOT NULL,
        due_time TEXT DEFAULT '',
        estimated_minutes INTEGER DEFAULT 30,
        completed_at TEXT,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_type TEXT NOT NULL,
        period_start TEXT NOT NULL,
        period_end TEXT NOT NULL,
        total_tasks INTEGER DEFAULT 0,
        completed_tasks INTEGER DEFAULT 0,
        completion_rate REAL DEFAULT 0.0,
        metrics_json TEXT DEFAULT '{}',
        ai_analysis TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nutrition_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        meal_type TEXT DEFAULT 'Tushlik',
        food_name TEXT NOT NULL,
        calories REAL DEFAULT 0.0,
        protein REAL DEFAULT 0.0,
        carbs REAL DEFAULT 0.0,
        fat REAL DEFAULT 0.0,
        weight_grams REAL DEFAULT 100.0,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        workout_type TEXT DEFAULT 'Zal / Kuch mashqlari',
        duration_minutes INTEGER DEFAULT 45,
        calories_burned REAL DEFAULT 0.0,
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        amount_ml INTEGER DEFAULT 250,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        icon TEXT DEFAULT 'tag',
        color TEXT DEFAULT 'indigo',
        created_at TEXT NOT NULL
    )
    """)

    # Seed default categories if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM categories")
    if cursor.fetchone()["cnt"] == 0:
        default_cats = [
            ("Ish", "briefcase", "indigo"),
            ("O'qish", "book-open", "blue"),
            ("Salomatlik", "activity", "emerald"),
            ("Shaxsiy", "user", "purple"),
            ("Sport", "dumbbell", "orange"),
            ("Moliya", "wallet", "amber"),
            ("Boshqa", "tag", "slate")
        ]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for c_name, c_icon, c_color in default_cats:
            cursor.execute(
                "INSERT INTO categories (name, icon, color, created_at) VALUES (?, ?, ?, ?)",
                (c_name, c_icon, c_color, now_str)
            )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telegram_subscribers (
        chat_id INTEGER PRIMARY KEY,
        user_name TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # Ensure reminded column exists in tasks
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN reminded INTEGER DEFAULT 0")
    except Exception:
        pass

    conn.commit()
    conn.close()


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def create_task(
    title: str,
    description: str = "",
    category: str = "Ish",
    priority: str = "O'rta",
    due_date: Optional[str] = None,
    due_time: str = "",
    estimated_minutes: int = 30,
    status: str = "Yangi"
) -> Dict[str, Any]:
    if not due_date:
        due_date = date.today().strftime("%Y-%m-%d")
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completed_at = now_str if status == "Bajarildi" else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, description, category, priority, status, due_date, due_time, estimated_minutes, completed_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, category, priority, status, due_date, due_time, estimated_minutes, completed_at, now_str))
    
    task_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)


def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def update_task(task_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    current = get_task(task_id)
    if not current:
        return None

    allowed_fields = [
        "title", "description", "category", "priority", 
        "status", "due_date", "due_time", "estimated_minutes"
    ]
    fields_to_update = []
    values = []

    for field in allowed_fields:
        if field in updates:
            fields_to_update.append(f"{field} = ?")
            values.append(updates[field])

    if "status" in updates:
        if updates["status"] == "Bajarildi" and current["status"] != "Bajarildi":
            fields_to_update.append("completed_at = ?")
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        elif updates["status"] != "Bajarildi":
            fields_to_update.append("completed_at = ?")
            values.append(None)

    if not fields_to_update:
        return current

    values.append(task_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE tasks SET {', '.join(fields_to_update)} WHERE id = ?", values)
    conn.commit()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)


def toggle_task(task_id: int) -> Optional[Dict[str, Any]]:
    current = get_task(task_id)
    if not current:
        return None
    new_status = "Yangi" if current["status"] == "Bajarildi" else "Bajarildi"
    return update_task(task_id, {"status": new_status})


def delete_task(task_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def list_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    date_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status:
        if status == "Ochiq":
            query += " AND status != 'Bajarildi'"
        else:
            query += " AND status = ?"
            params.append(status)

    if category:
        query += " AND category = ?"
        params.append(category)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    if date_filter:
        query += " AND due_date = ?"
        params.append(date_filter)

    if start_date:
        query += " AND due_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND due_date <= ?"
        params.append(end_date)

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term])

    query += " ORDER BY due_date ASC, CASE priority WHEN 'Yuqori' THEN 1 WHEN 'O''rta' THEN 2 ELSE 3 END, due_time ASC, id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_period_stats(start_date: str, end_date: str) -> Dict[str, Any]:
    tasks = list_tasks(start_date=start_date, end_date=end_date)
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Bajarildi")
    in_progress = sum(1 for t in tasks if t["status"] == "Bajarilmoqda")
    pending = sum(1 for t in tasks if t["status"] == "Yangi")
    
    today_str = date.today().strftime("%Y-%m-%d")
    overdue = sum(1 for t in tasks if t["status"] != "Bajarildi" and t["due_date"] < today_str)
    
    rate = round((completed / total * 100), 1) if total > 0 else 0.0

    by_category: Dict[str, Dict[str, int]] = {}
    by_priority: Dict[str, Dict[str, int]] = {}
    by_date: Dict[str, Dict[str, int]] = {}

    for t in tasks:
        cat = t["category"] or "Boshqa"
        prio = t["priority"] or "O'rta"
        d = t["due_date"]

        if cat not in by_category:
            by_category[cat] = {"total": 0, "completed": 0}
        by_category[cat]["total"] += 1
        if t["status"] == "Bajarildi":
            by_category[cat]["completed"] += 1

        if prio not in by_priority:
            by_priority[prio] = {"total": 0, "completed": 0}
        by_priority[prio]["total"] += 1
        if t["status"] == "Bajarildi":
            by_priority[prio]["completed"] += 1

        if d not in by_date:
            by_date[d] = {"total": 0, "completed": 0}
        by_date[d]["total"] += 1
        if t["status"] == "Bajarildi":
            by_date[d]["completed"] += 1

    return {
        "period_start": start_date,
        "period_end": end_date,
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "pending_tasks": pending,
        "overdue_tasks": overdue,
        "completion_rate": rate,
        "by_category": by_category,
        "by_priority": by_priority,
        "by_date": by_date,
        "tasks": tasks
    }


def save_report(report_type: str, period_start: str, period_end: str, summary: Dict[str, Any], ai_analysis: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO reports (report_type, period_start, period_end, total_tasks, completed_tasks, completion_rate, metrics_json, ai_analysis, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_type,
        period_start,
        period_end,
        summary.get("total_tasks", 0),
        summary.get("completed_tasks", 0),
        summary.get("completion_rate", 0.0),
        json.dumps(summary, ensure_ascii=False),
        ai_analysis,
        now_str
    ))
    
    report_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    res = row_to_dict(row)
    res["metrics_json"] = json.loads(res["metrics_json"])
    return res


def get_latest_report(report_type: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM reports WHERE report_type = ? ORDER BY id DESC LIMIT 1
    """, (report_type,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = row_to_dict(row)
    try:
        res["metrics_json"] = json.loads(res["metrics_json"])
    except:
        pass
    return res


def get_setting(key: str, default: str = "") -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def add_nutrition_log(
    date_str: str,
    meal_type: str,
    food_name: str,
    calories: float,
    protein: float = 0.0,
    carbs: float = 0.0,
    fat: float = 0.0,
    weight_grams: float = 100.0
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO nutrition_logs (date, meal_type, food_name, calories, protein, carbs, fat, weight_grams, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, meal_type, food_name, round(calories, 1), round(protein, 1), round(carbs, 1), round(fat, 1), round(weight_grams, 1), now_str))
    log_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM nutrition_logs WHERE id = ?", (log_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)


def list_nutrition_logs(date_str: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nutrition_logs WHERE date = ? ORDER BY id ASC", (date_str,))
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def delete_nutrition_log(log_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nutrition_logs WHERE id = ?", (log_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def add_workout_log(
    date_str: str,
    workout_type: str,
    duration_minutes: int,
    calories_burned: float,
    notes: str = ""
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO workout_logs (date, workout_type, duration_minutes, calories_burned, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, workout_type, duration_minutes, round(calories_burned, 1), notes, now_str))
    log_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM workout_logs WHERE id = ?", (log_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)


def list_workout_logs(date_str: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workout_logs WHERE date = ? ORDER BY id DESC", (date_str,))
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def delete_workout_log(log_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workout_logs WHERE id = ?", (log_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def add_water_log(date_str: str, amount_ml: int = 250) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO water_logs (date, amount_ml, created_at)
        VALUES (?, ?, ?)
    """, (date_str, amount_ml, now_str))
    conn.commit()
    conn.close()
    return get_water_total(date_str)


def get_water_total(date_str: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount_ml) as total FROM water_logs WHERE date = ?", (date_str,))
    row = cursor.fetchone()
    conn.close()
    return row["total"] or 0 if row else 0


def reset_water_log(date_str: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM water_logs WHERE date = ?", (date_str,))
    conn.commit()
    conn.close()
    return True


def get_fitness_profile() -> Dict[str, Any]:
    target_calories = int(get_setting("target_calories", "2200"))
    target_water_ml = int(get_setting("target_water_ml", "2500"))
    target_protein_g = int(get_setting("target_protein_g", "130"))
    goal_type = get_setting("goal_type", "Mushak massasi yig'ish")
    current_weight_kg = float(get_setting("current_weight_kg", "75.0"))
    return {
        "target_calories": target_calories,
        "target_water_ml": target_water_ml,
        "target_protein_g": target_protein_g,
        "goal_type": goal_type,
        "current_weight_kg": current_weight_kg
    }


def save_fitness_profile(profile: Dict[str, Any]):
    if "target_calories" in profile:
        set_setting("target_calories", str(profile["target_calories"]))
    if "target_water_ml" in profile:
        set_setting("target_water_ml", str(profile["target_water_ml"]))
    if "target_protein_g" in profile:
        set_setting("target_protein_g", str(profile["target_protein_g"]))
    if "goal_type" in profile:
        set_setting("goal_type", str(profile["goal_type"]))
    if "current_weight_kg" in profile:
        set_setting("current_weight_kg", str(profile["current_weight_kg"]))


def get_fitness_summary(date_str: str) -> Dict[str, Any]:
    meals = list_nutrition_logs(date_str)
    workouts = list_workout_logs(date_str)
    water_ml = get_water_total(date_str)
    profile = get_fitness_profile()

    consumed_calories = round(sum(m["calories"] for m in meals), 1)
    total_protein = round(sum(m["protein"] for m in meals), 1)
    total_carbs = round(sum(m["carbs"] for m in meals), 1)
    total_fat = round(sum(m["fat"] for m in meals), 1)

    burned_calories = round(sum(w["calories_burned"] for w in workouts), 1)
    total_workout_mins = sum(w["duration_minutes"] for w in workouts)

    # Net Calorie: Consumed - Burned
    net_calories = round(consumed_calories - burned_calories, 1)
    remaining_calories = round(profile["target_calories"] - net_calories, 1)

    # Group meals by meal_type
    meals_by_type = {
        "Nonushta": [],
        "Tushlik": [],
        "Kechki ovqat": [],
        "Gazak": []
    }
    for m in meals:
        mt = m["meal_type"]
        if mt not in meals_by_type:
            meals_by_type[mt] = []
        meals_by_type[mt].append(m)

    return {
        "date": date_str,
        "profile": profile,
        "consumed_calories": consumed_calories,
        "burned_calories": burned_calories,
        "net_calories": net_calories,
        "remaining_calories": remaining_calories,
        "total_protein": total_protein,
        "total_carbs": total_carbs,
        "total_fat": total_fat,
        "water_ml": water_ml,
        "total_workout_mins": total_workout_mins,
        "meals": meals,
        "meals_by_type": meals_by_type,
        "workouts": workouts
    }


def list_categories() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def create_category(name: str, icon: str = "tag", color: str = "indigo") -> Optional[Dict[str, Any]]:
    name = name.strip()
    if not name:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "INSERT INTO categories (name, icon, color, created_at) VALUES (?, ?, ?, ?)",
            (name, icon, color, now_str)
        )
        cat_id = cursor.lastrowid
        conn.commit()
        cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
        row = cursor.fetchone()
        conn.close()
        return row_to_dict(row)
    except sqlite3.IntegrityError:
        conn.close()
        # Already exists
        cursor = get_db_connection().cursor()
        cursor.execute("SELECT * FROM categories WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row_to_dict(row) if row else None


def delete_category(category_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def add_telegram_subscriber(chat_id: int, user_name: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO telegram_subscribers (chat_id, user_name, is_active, created_at)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(chat_id) DO UPDATE SET is_active = 1, user_name = ?
        """,
        (chat_id, user_name, now_str, user_name)
    )
    conn.commit()
    conn.close()


def get_active_telegram_subscribers() -> List[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM telegram_subscribers WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    return [r["chat_id"] for r in rows]


def get_due_tasks_for_reminders(current_time_str: str) -> List[Dict[str, Any]]:
    today_str = date.today().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM tasks
        WHERE due_date = ?
          AND status != 'Bajarildi'
          AND (reminded IS NULL OR reminded = 0)
          AND due_time != ''
          AND due_time <= ?
        ORDER BY due_time ASC
        """,
        (today_str, current_time_str)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def mark_task_reminded(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET reminded = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)

