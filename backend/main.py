import os
import sys
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

# Ensure backend package can be imported
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend import database
from backend import ai_agent
from backend import calendar_service

app = FastAPI(
    title="SmartTask AI",
    description="Aqlli Vazifalar Boshqaruvi va AI Tahliliy Hisobotlar Tizimi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


# Pydantic Schemas
class TaskCreateSchema(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    category: Optional[str] = "Ish"
    priority: Optional[str] = "O'rta"
    status: Optional[str] = "Yangi"
    due_date: Optional[str] = None
    due_time: Optional[str] = ""
    estimated_minutes: Optional[int] = 30


class TaskUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    estimated_minutes: Optional[int] = None


class ParseTaskRequest(BaseModel):
    text: str = Field(..., min_length=2)


class AICoachRequest(BaseModel):
    message: str = Field(..., min_length=1)


class SettingRequest(BaseModel):
    key: str
    value: str


class NutritionCreateSchema(BaseModel):
    food_name: str = Field(..., min_length=1)
    meal_type: Optional[str] = "Tushlik"
    calories: float = Field(..., ge=0)
    protein: Optional[float] = 0.0
    carbs: Optional[float] = 0.0
    fat: Optional[float] = 0.0
    weight_grams: Optional[float] = 100.0
    date: Optional[str] = None


class WorkoutCreateSchema(BaseModel):
    workout_type: Optional[str] = "Zal / Kuch mashqlari"
    duration_minutes: int = Field(..., gt=0)
    calories_burned: Optional[float] = None
    notes: Optional[str] = ""
    date: Optional[str] = None


class WaterAddSchema(BaseModel):
    amount_ml: int = Field(250, gt=0)
    date: Optional[str] = None


class FitnessProfileSchema(BaseModel):
    target_calories: Optional[int] = None
    target_water_ml: Optional[int] = None
    target_protein_g: Optional[int] = None
    goal_type: Optional[str] = None
    current_weight_kg: Optional[float] = None


class ParseFoodRequest(BaseModel):
    text: str = Field(..., min_length=2)


class ParseWorkoutRequest(BaseModel):
    text: str = Field(..., min_length=2)


class CategoryCreateSchema(BaseModel):
    name: str = Field(..., min_length=1)
    icon: Optional[str] = "tag"
    color: Optional[str] = "indigo"


def seed_demo_data_if_empty():
    existing = database.list_tasks()
    if existing:
        return
    
    today = date.today().strftime("%Y-%m-%d")
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    demo_tasks = [
        {
            "title": "SmartTask AI tizimini ishga tushirish va ko'rib chiqish",
            "description": "Yangi tizim imkoniyatlari, vazifalar va hisobotlar bo'limini test qilish",
            "category": "Ish",
            "priority": "Yuqori",
            "status": "Bajarildi",
            "due_date": today,
            "due_time": "10:00",
            "estimated_minutes": 20
        },
        {
            "title": "Haftalik ish rejasini shakllantirish",
            "description": "Eng muhim 3 ta strategik vazifani belgilab olish",
            "category": "Ish",
            "priority": "Yuqori",
            "status": "Bajarilmoqda",
            "due_date": today,
            "due_time": "14:30",
            "estimated_minutes": 45
        },
        {
            "title": "30 daqiqa kitob mutolaasi qilish",
            "description": "Shaxsiy rivojlanish va diqqatni jamlash uchun",
            "category": "O'qish",
            "priority": "O'rta",
            "status": "Yangi",
            "due_date": today,
            "due_time": "20:00",
            "estimated_minutes": 30
        },
        {
            "title": "Toza havoda 5 km piyoda yurish / yugurish",
            "description": "Salomatlik va tetiklik uchun jismoniy mashq",
            "category": "Salomatlik",
            "priority": "Past",
            "status": "Yangi",
            "due_date": today,
            "due_time": "18:00",
            "estimated_minutes": 40
        },
        {
            "title": "O'tgan haftaning moliyaviy hisob-kitobini yakunlash",
            "description": "Daromad va xarajatlarni hisoblash",
            "category": "Ish",
            "priority": "Yuqori",
            "status": "Bajarildi",
            "due_date": yesterday,
            "due_time": "16:00",
            "estimated_minutes": 60
        },
        {
            "title": "Ingliz tili so'z boyligini oshirish (20 ta yangi so'z)",
            "description": "Flashcard orqali yangi iboralarni yodlash",
            "category": "O'qish",
            "priority": "O'rta",
            "status": "Yangi",
            "due_date": tomorrow,
            "due_time": "11:00",
            "estimated_minutes": 25
        }
    ]

    for item in demo_tasks:
        database.create_task(**item)

    # Seed demo nutrition and workout
    existing_meals = database.list_nutrition_logs(today)
    if not existing_meals:
        database.add_nutrition_log(today, "Nonushta", "Suli yormasi (ovsyanka) va 2 ta tuxum", 330.0, 22.0, 35.0, 11.0, 220.0)
        database.add_nutrition_log(today, "Tushlik", "Tovuq filesi va grechka", 480.0, 52.0, 42.0, 6.5, 350.0)
        database.add_nutrition_log(today, "Gazak", "1 ta banan va 30g yong'oq", 290.0, 5.8, 31.0, 19.3, 150.0)
        database.add_workout_log(today, "Zal / Kuch mashqlari", 50, 375.0, "Ko'krak va qo'l mushaklari mashqlari")
        database.add_water_log(today, 1250)


@app.on_event("startup")
def on_startup():
    database.init_db()
    seed_demo_data_if_empty()


# API Endpoints
@app.get("/api/tasks")
def get_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    date_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None
):
    tasks = database.list_tasks(
        status=status,
        category=category,
        priority=priority,
        date_filter=date_filter,
        start_date=start_date,
        end_date=end_date,
        search=search
    )
    return {"tasks": tasks, "count": len(tasks)}


@app.post("/api/tasks")
def add_task(task_in: TaskCreateSchema):
    new_task = database.create_task(
        title=task_in.title,
        description=task_in.description or "",
        category=task_in.category or "Ish",
        priority=task_in.priority or "O'rta",
        status=task_in.status or "Yangi",
        due_date=task_in.due_date,
        due_time=task_in.due_time or "",
        estimated_minutes=task_in.estimated_minutes or 30
    )
    return {"task": new_task, "message": "Vazifa muvaffaqiyatli qo'shildi"}


@app.get("/api/tasks/{task_id}")
def get_single_task(task_id: int):
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    return {"task": task}


@app.put("/api/tasks/{task_id}")
def edit_task(task_id: int, updates: TaskUpdateSchema):
    data = updates.model_dump(exclude_unset=True)
    updated = database.update_task(task_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    return {"task": updated, "message": "Vazifa yangilandi"}


@app.patch("/api/tasks/{task_id}/toggle")
def toggle_task_status(task_id: int):
    toggled = database.toggle_task(task_id)
    if not toggled:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    return {"task": toggled, "message": f"Status '{toggled['status']}' holatiga o'zgartirildi"}


@app.delete("/api/tasks/{task_id}")
def remove_task(task_id: int):
    success = database.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    return {"success": True, "message": "Vazifa muvaffaqiyatli o'chirildi"}


@app.get("/api/stats/overview")
def get_stats_overview():
    today_str = date.today().strftime("%Y-%m-%d")
    week_start = (date.today() - timedelta(days=6)).strftime("%Y-%m-%d")
    month_start = f"{date.today().year}-{date.today().month:02d}-01"

    today_stats = database.get_period_stats(today_str, today_str)
    week_stats = database.get_period_stats(week_start, today_str)
    month_stats = database.get_period_stats(month_start, today_str)

    all_tasks = database.list_tasks()
    total_all = len(all_tasks)
    total_completed = sum(1 for t in all_tasks if t["status"] == "Bajarildi")

    return {
        "today": today_stats,
        "weekly": week_stats,
        "monthly": month_stats,
        "overall": {
            "total": total_all,
            "completed": total_completed,
            "completion_rate": round(total_completed / total_all * 100, 1) if total_all > 0 else 0
        }
    }


@app.get("/api/reports/daily")
def get_daily_report(date_str: Optional[str] = Query(None, alias="date")):
    target = date_str or date.today().strftime("%Y-%m-%d")
    report = ai_agent.generate_daily_report(target)
    return report


@app.get("/api/reports/weekly")
def get_weekly_report(end_date: Optional[str] = None):
    report = ai_agent.generate_weekly_report(end_date)
    return report


@app.get("/api/reports/monthly")
def get_monthly_report(year: Optional[int] = None, month: Optional[int] = None):
    now = date.today()
    target_year = year or now.year
    target_month = month or now.month
    report = ai_agent.generate_monthly_report(target_year, target_month)
    return report


@app.post("/api/ai/parse-task")
def parse_task(payload: ParseTaskRequest):
    parsed = ai_agent.parse_task_nlp(payload.text)
    return {"parsed": parsed}


@app.post("/api/ai/coach")
def coach_chat(payload: AICoachRequest):
    response = ai_agent.chat_coach(payload.message)
    return {"reply": response}


@app.get("/api/settings")
def get_settings():
    api_key = database.get_setting("gemini_api_key", "")
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else ("O'rnatilgan" if api_key else "")
    
    tg_token = database.get_setting("telegram_bot_token", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
    masked_tg = f"{tg_token[:6]}...{tg_token[-4:]}" if len(tg_token) > 10 else ("O'rnatilgan" if tg_token else "")

    web_app_url = database.get_setting("web_app_url", "")

    return {
        "gemini_api_key_set": bool(api_key),
        "gemini_api_key_masked": masked_key,
        "telegram_bot_token_set": bool(tg_token),
        "telegram_bot_token_masked": masked_tg,
        "web_app_url": web_app_url
    }


@app.post("/api/settings")
def save_setting(payload: SettingRequest):
    database.set_setting(payload.key, payload.value)
    return {"success": True, "message": "Sozlama saqlandi"}


# Category Management Endpoints
@app.get("/api/categories")
def get_categories():
    categories = database.list_categories()
    return {"categories": categories}


@app.post("/api/categories")
def add_category(item: CategoryCreateSchema):
    created = database.create_category(
        name=item.name,
        icon=item.icon or "tag",
        color=item.color or "indigo"
    )
    if not created:
        raise HTTPException(status_code=400, detail="Kategoriya yaratib bo'lmadi")
    return {"category": created, "message": "Kategoriya muvaffaqiyatli qo'shildi"}


@app.delete("/api/categories/{cat_id}")
def remove_category(cat_id: int):
    success = database.delete_category(cat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    return {"success": True, "message": "Kategoriya o'chirildi"}


# Fitness & Nutrition Endpoints
@app.get("/api/nutrition")
def get_nutrition(date_str: Optional[str] = Query(None, alias="date")):
    target = date_str or date.today().strftime("%Y-%m-%d")
    logs = database.list_nutrition_logs(target)
    return {"meals": logs, "date": target}


@app.post("/api/nutrition")
def add_nutrition(item: NutritionCreateSchema):
    target_date = item.date or date.today().strftime("%Y-%m-%d")
    created = database.add_nutrition_log(
        date_str=target_date,
        meal_type=item.meal_type or "Tushlik",
        food_name=item.food_name,
        calories=item.calories,
        protein=item.protein or 0.0,
        carbs=item.carbs or 0.0,
        fat=item.fat or 0.0,
        weight_grams=item.weight_grams or 100.0
    )
    return {"meal": created, "message": "Taom muvaffaqiyatli qo'shildi"}


@app.delete("/api/nutrition/{log_id}")
def delete_nutrition(log_id: int):
    success = database.delete_nutrition_log(log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Taom yozuvi topilmadi")
    return {"success": True, "message": "Taom yozuvi o'chirildi"}


@app.get("/api/workout")
def get_workouts(date_str: Optional[str] = Query(None, alias="date")):
    target = date_str or date.today().strftime("%Y-%m-%d")
    logs = database.list_workout_logs(target)
    return {"workouts": logs, "date": target}


@app.post("/api/workout")
def add_workout(item: WorkoutCreateSchema):
    target_date = item.date or date.today().strftime("%Y-%m-%d")
    profile = database.get_fitness_profile()
    weight = profile.get("current_weight_kg", 75.0)

    if item.calories_burned is not None and item.calories_burned > 0:
        burned = item.calories_burned
    else:
        burned = ai_agent.estimate_workout_calories(
            item.workout_type or "Zal / Kuch mashqlari",
            item.duration_minutes,
            weight
        )

    created = database.add_workout_log(
        date_str=target_date,
        workout_type=item.workout_type or "Zal / Kuch mashqlari",
        duration_minutes=item.duration_minutes,
        calories_burned=burned,
        notes=item.notes or ""
    )
    return {"workout": created, "message": "Mashg'ulot muvaffaqiyatli saqlandi"}


@app.delete("/api/workout/{log_id}")
def delete_workout(log_id: int):
    success = database.delete_workout_log(log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mashg'ulot topilmadi")
    return {"success": True, "message": "Mashg'ulot yozuvi o'chirildi"}


@app.get("/api/water")
def get_water(date_str: Optional[str] = Query(None, alias="date")):
    target = date_str or date.today().strftime("%Y-%m-%d")
    total = database.get_water_total(target)
    return {"water_ml": total, "date": target}


@app.post("/api/water/add")
def add_water(payload: WaterAddSchema):
    target_date = payload.date or date.today().strftime("%Y-%m-%d")
    total = database.add_water_log(target_date, payload.amount_ml)
    return {"water_ml": total, "message": f"+{payload.amount_ml}ml suv qo'shildi"}


@app.post("/api/water/reset")
def reset_water(payload: WaterAddSchema):
    target_date = payload.date or date.today().strftime("%Y-%m-%d")
    database.reset_water_log(target_date)
    return {"water_ml": 0, "message": "Suv hisobi yangilandi"}


@app.get("/api/fitness/summary")
def get_fitness_summary_endpoint(date_str: Optional[str] = Query(None, alias="date")):
    target = date_str or date.today().strftime("%Y-%m-%d")
    summary = database.get_fitness_summary(target)
    return summary


@app.get("/api/fitness/ai-report")
def get_fitness_ai_report(date_str: Optional[str] = Query(None, alias="date")):
    target = date_str or date.today().strftime("%Y-%m-%d")
    report_text = ai_agent.generate_fitness_ai_report(target)
    return {"date": target, "report": report_text}


@app.get("/api/fitness/profile")
def get_fitness_profile_endpoint():
    profile = database.get_fitness_profile()
    return {"profile": profile}


@app.post("/api/fitness/profile")
def update_fitness_profile(profile_in: FitnessProfileSchema):
    data = profile_in.model_dump(exclude_unset=True)
    database.save_fitness_profile(data)
    updated = database.get_fitness_profile()
    return {"profile": updated, "message": "Fitnes maqsadlari saqlandi"}


@app.post("/api/ai/parse-food")
def parse_food(payload: ParseFoodRequest):
    parsed = ai_agent.parse_food_nlp(payload.text)
    return {"parsed": parsed}


@app.post("/api/ai/parse-workout")
def parse_workout(payload: ParseWorkoutRequest):
    profile = database.get_fitness_profile()
    parsed = ai_agent.parse_workout_nlp(payload.text, profile.get("current_weight_kg", 75.0))
    return {"parsed": parsed}


# ---------------- Calendar Integration (RFC 5545 & Google Calendar) ----------------
@app.get("/api/calendar/tasks.ics")
def get_calendar_ics(status: Optional[str] = Query("Ochiq")):
    """
    Telefon va kompyuter kalendarlari (iOS Calendar, Google Calendar, Outlook)
    uchun RFC 5545 standartidagi .ics fayl oqimini qaytaradi.
    Har bir vazifada 15 daqiqa oldin eslatma beruvchi VALARM signali bor.
    """
    tasks = database.list_tasks(status=status if status != "all" else None)
    # Faqat muddati (due_date) bor vazifalarni kalendarga qo'shamiz
    calendar_tasks = [t for t in tasks if t.get("due_date")]
    ical_content = calendar_service.generate_ical_feed(calendar_tasks, "SmartTask AI Vazifalari")
    
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": 'attachment; filename="smarttask_tasks.ics"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Type": "text/calendar; charset=utf-8"
        }
    )


@app.get("/api/calendar/task/{task_id}/google-url")
def get_task_google_calendar_url(task_id: int):
    """
    Alohida bitta vazifani Google Calendar veb-interfeysida 1 bosishda
    qo'shish uchun maxsus tayyorlangan havolani qaytaradi.
    """
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    url = calendar_service.generate_google_calendar_url(task)
    return {"task_id": task_id, "google_calendar_url": url}


# Static Files & Frontend SPA
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html hali tayyor emas"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
