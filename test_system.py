import os
import sys
import unittest
from datetime import date, timedelta

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from backend import database
from backend import ai_agent
from fastapi.testclient import TestClient
from backend.main import app

class TestSmartTaskAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_db()

    def test_01_database_task_crud(self):
        # Create
        task = database.create_task(
            title="Unit Test Vazifasi",
            description="Sinov uchun tavsif",
            category="Ish",
            priority="Yuqori",
            due_date=date.today().strftime("%Y-%m-%d"),
            due_time="11:30"
        )
        self.assertIsNotNone(task["id"])
        self.assertEqual(task["title"], "Unit Test Vazifasi")
        task_id = task["id"]

        # Read
        fetched = database.get_task(task_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["priority"], "Yuqori")

        # Toggle status
        toggled = database.toggle_task(task_id)
        self.assertEqual(toggled["status"], "Bajarildi")
        self.assertIsNotNone(toggled["completed_at"])

        # Update
        updated = database.update_task(task_id, {"title": "O'zgartirilgan Vazifa"})
        self.assertEqual(updated["title"], "O'zgartirilgan Vazifa")

        # Delete
        deleted = database.delete_task(task_id)
        self.assertTrue(deleted)
        self.assertIsNone(database.get_task(task_id))

    def test_02_nlp_parser(self):
        text = "Ertaga soat 16:30 da hisobot tayyorlash, juda muhim ish"
        parsed = ai_agent.parse_task_nlp(text)
        self.assertIn("title", parsed)
        self.assertIn("category", parsed)
        self.assertEqual(parsed["priority"], "Yuqori")
        self.assertEqual(parsed["due_time"], "16:30")
        tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(parsed["due_date"], tomorrow_str)

    def test_03_daily_report_generation(self):
        today = date.today().strftime("%Y-%m-%d")
        report = ai_agent.generate_daily_report(today)
        self.assertIn("stats", report)
        self.assertIn("ai_analysis", report)
        self.assertIn("grade", report)

    def test_04_weekly_report_generation(self):
        today = date.today().strftime("%Y-%m-%d")
        report = ai_agent.generate_weekly_report(today)
        self.assertIn("stats", report)
        self.assertIn("ai_analysis", report)
        self.assertEqual(report["report_type"], "weekly")

    def test_05_monthly_report_generation(self):
        now = date.today()
        report = ai_agent.generate_monthly_report(now.year, now.month)
        self.assertIn("stats", report)
        self.assertIn("ai_analysis", report)
        self.assertEqual(report["report_type"], "monthly")

    def test_06_fastapi_endpoints(self):
        client = TestClient(app)
        
        # Test GET /api/tasks
        res = client.get("/api/tasks")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("tasks", data)

        # Test GET /api/stats/overview
        res_stats = client.get("/api/stats/overview")
        self.assertEqual(res_stats.status_code, 200)
        self.assertIn("today", res_stats.json())

        # Test POST /api/ai/coach
        res_coach = client.post("/api/ai/coach", json={"message": "Vaqtni qanday taqsimlay?"})
        self.assertEqual(res_coach.status_code, 200)
        self.assertIn("reply", res_coach.json())

        # Test Static Index
        res_index = client.get("/")
        self.assertEqual(res_index.status_code, 200)

    def test_07_nutrition_and_workout_db(self):
        today = date.today().strftime("%Y-%m-%d")
        
        # Add food
        food = database.add_nutrition_log(
            date_str=today,
            meal_type="Tushlik",
            food_name="Tovuq va grechka",
            calories=450.0,
            protein=48.0,
            carbs=40.0,
            fat=6.0,
            weight_grams=300.0
        )
        self.assertIsNotNone(food["id"])
        self.assertEqual(food["food_name"], "Tovuq va grechka")

        # Add workout
        workout = database.add_workout_log(
            date_str=today,
            workout_type="Zal / Kuch mashqlari",
            duration_minutes=45,
            calories_burned=337.5,
            notes="Sinov mashg'uloti"
        )
        self.assertIsNotNone(workout["id"])

        # Add water
        water_tot = database.add_water_log(today, 500)
        self.assertGreaterEqual(water_tot, 500)

        # Get summary
        summary = database.get_fitness_summary(today)
        self.assertGreaterEqual(summary["consumed_calories"], 450.0)
        self.assertGreaterEqual(summary["burned_calories"], 337.5)
        self.assertIn("meals_by_type", summary)

    def test_08_food_and_workout_nlp(self):
        # NLP Food parsing
        food_text = "Tushlikda 200gr tovuq va 150gr grechka yedim"
        parsed_food = ai_agent.parse_food_nlp(food_text)
        self.assertIn("calories", parsed_food)
        self.assertIn("protein", parsed_food)
        self.assertGreater(parsed_food["calories"], 0)
        self.assertGreater(parsed_food["protein"], 0)

        # NLP Workout parsing
        workout_text = "Bugun zalda 50 daqiqa mashg'ulot qildim"
        parsed_workout = ai_agent.parse_workout_nlp(workout_text)
        self.assertEqual(parsed_workout["workout_type"], "Zal / Kuch mashqlari")
        self.assertEqual(parsed_workout["duration_minutes"], 50)
        self.assertGreater(parsed_workout["calories_burned"], 0)

    def test_09_fitness_api_endpoints(self):
        client = TestClient(app)
        today = date.today().strftime("%Y-%m-%d")

        # GET /api/fitness/summary
        res = client.get(f"/api/fitness/summary?date={today}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("consumed_calories", data)
        self.assertIn("net_calories", data)

        # POST /api/nutrition
        res_food = client.post("/api/nutrition", json={
            "food_name": "Nonushta tvorog",
            "meal_type": "Nonushta",
            "calories": 220.0,
            "protein": 28.0,
            "carbs": 6.0,
            "fat": 4.0,
            "date": today
        })
        self.assertEqual(res_food.status_code, 200)
        self.assertIn("meal", res_food.json())

        # POST /api/water/add
        res_water = client.post("/api/water/add", json={"amount_ml": 250, "date": today})
        self.assertEqual(res_water.status_code, 200)
        self.assertIn("water_ml", res_water.json())

        # POST /api/ai/parse-food
        res_nlp = client.post("/api/ai/parse-food", json={"text": "2 ta tuxum va 1 ta banan yedim"})
        self.assertEqual(res_nlp.status_code, 200)
        self.assertIn("parsed", res_nlp.json())

    def test_10_categories_crud_api(self):
        client = TestClient(app)

        # GET /api/categories
        res = client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("categories", data)
        self.assertGreaterEqual(len(data["categories"]), 1)

        # POST /api/categories
        new_cat = client.post("/api/categories", json={
            "name": "Dizayn & San'at",
            "icon": "rocket",
            "color": "indigo"
        })
        self.assertEqual(new_cat.status_code, 200)
        cat_data = new_cat.json().get("category")
        self.assertIsNotNone(cat_data)
        cat_id = cat_data["id"]
        self.assertEqual(cat_data["name"], "Dizayn & San'at")

        # DELETE /api/categories/{cat_id}
        del_res = client.delete(f"/api/categories/{cat_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json().get("success"))

    def test_11_calendar_endpoints(self):
        client = TestClient(app)

        # Create a task with due date and time
        task = database.create_task(
            title="Kalendar Sinov Vazifasi",
            description="iCalendar test",
            due_date=date.today().strftime("%Y-%m-%d"),
            due_time="15:30",
            category="Ish"
        )
        task_id = task["id"]

        # GET /api/calendar/tasks.ics
        res = client.get("/api/calendar/tasks.ics")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/calendar", res.headers.get("content-type", ""))
        self.assertIn("BEGIN:VCALENDAR", res.text)
        self.assertIn("BEGIN:VEVENT", res.text)
        self.assertIn("BEGIN:VALARM", res.text)
        self.assertIn("TRIGGER:-PT15M", res.text)
        self.assertIn("END:VCALENDAR", res.text)

        # GET /api/calendar/task/{task_id}/google-url
        res_g = client.get(f"/api/calendar/task/{task_id}/google-url")
        self.assertEqual(res_g.status_code, 200)
        g_data = res_g.json()
        self.assertIn("google_calendar_url", g_data)
        self.assertIn("calendar.google.com", g_data["google_calendar_url"])

        # Clean up
        database.delete_task(task_id)

    def test_12_calorie_accuracy(self):
        # 1. Chicken breast + buckwheat
        res1 = ai_agent.parse_food_nlp("200gr tovuq filesi va 150gr grechka")
        self.assertAlmostEqual(res1["calories"], 502.5, delta=15.0)
        self.assertAlmostEqual(res1["protein"], 69.0, delta=10.0)

        # 2. Lag'mon + Somsa
        res2 = ai_agent.parse_food_nlp("1 kosa lag'mon va 2 dona somsa")
        self.assertAlmostEqual(res2["calories"], 1160.0, delta=30.0)

        # 3. Eggs + banana
        res3 = ai_agent.parse_food_nlp("2 ta tuxum va 1 ta banan")
        self.assertAlmostEqual(res3["calories"], 260.0, delta=20.0)

        # 4. Check no false substring matching (e.g. go'sht shouldn't match osh)
        res4 = ai_agent.parse_food_nlp("150gr qaynatilgan mol go'shti")
        food_names = [f["name"] for f in res4.get("matched_foods", [])]
        self.assertNotIn("osh", food_names)

    def test_13_telegram_subscribers_db(self):
        test_chat_id = 999888777
        database.add_telegram_subscriber(test_chat_id, "Test User")
        subs = database.get_active_telegram_subscribers()
        self.assertIn(test_chat_id, subs)

    def test_14_samarkand_prayer_service(self):
        from backend import prayer_service
        # Test fetching timings
        timings = prayer_service.fetch_samarkand_prayer_times()
        for p in ["Bomdod", "Peshin", "Asr", "Shom", "Xufton"]:
            self.assertIn(p, timings)
            self.assertEqual(len(timings[p]), 5)  # HH:MM format

        # Test auto scheduling tasks
        created = prayer_service.auto_schedule_samarkand_prayers()
        # Verify tasks created in database
        today = date.today().strftime("%Y-%m-%d")
        tasks = database.list_tasks(date_filter=today, category="Ibodat")
        prayer_titles = [t["title"] for t in tasks]
        self.assertTrue(any("Bomdod" in t for t in prayer_titles))
        self.assertTrue(any("Peshin" in t for t in prayer_titles))
        self.assertTrue(any("Asr" in t for t in prayer_titles))
        self.assertTrue(any("Shom" in t for t in prayer_titles))
        self.assertTrue(any("Xufton" in t for t in prayer_titles))

        # Test API endpoint
        client = TestClient(app)
        res = client.get("/api/prayer/timings")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["city"], "Samarkand")


if __name__ == "__main__":
    unittest.main()



