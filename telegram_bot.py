import os
import sys
import io
import asyncio
import logging
from datetime import date, datetime

# Setup project path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend import database
from backend import ai_agent
from backend import calendar_service

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp, MenuButtonCommands, MenuButtonDefault
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_bot_token() -> str:
    # 1. Check database setting
    token = database.get_setting("telegram_bot_token", "")
    if token:
        return token.strip()
    # 2. Check environment variable
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


async def safe_reply(update: Update, text: str, reply_markup=None):
    if not update or not update.message:
        return

    # Foydalanuvchini bildirishnomalar ro'yxatiga avtomatik qo'shish
    if update.effective_chat:
        user_name = update.effective_user.first_name if update.effective_user else ""
        try:
            database.add_telegram_subscriber(update.effective_chat.id, user_name)
        except Exception:
            pass

    try:
        if reply_markup:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Markdown reply failed, falling back to plain text: {e}")
        try:
            if reply_markup:
                await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text)
        except Exception as e2:
            logger.error(f"Critical reply error: {e2}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name if update.effective_user else "Do'stim"
    
    welcome_text = f"""Assalomu alaykum, {user_name}! 🚀
Men sizning **SmartTask AI & Fitnes** shaxsiy yordamchingizman.

Siz menga to'g'ridan-to'g'ri yozishingiz mumkin:
📌 **Vazifalar:**
- Shunchaki yozing: *"Ertaga soat 15:00 da hisobot topshirish, muhim ish"*
- AI o'zi uni sana va vaqti bilan saytingizdagi jadvalga kiritadi.

💪 **Taom va Kaloriya:**
- Shunchaki yozing: *"Tushlikda 200gr tovuq va 150gr grechka yedim"*
- Yoki: `/taom 2 ta tuxum va 1 ta banan`
- AI uning kaloriyasi va oqsili (protein)ni hisoblab saqlaydi!

🏋️ **Sport Mashg'ulotlari:**
- `/mashq Zalda 50 daqiqa mashg'ulot qildim`
- Yoqilgan kaloriya avtomatik hisoblanadi.

💧 **Suv Nazorati:**
- `/suv` — +250ml suv qo'shish

📊 **Hisobotlar va Kalendar:**
- `/bugun` — Bugungi vazifalar va kaloriya balansi
- `/kalendar` — Vazifalarni telefon kalendariga ulash (.ics)
- `/eslatma` — Bildirishnomalar holati
- `/haftalik` — Haftalik unumdorlik tahlili
- `/yordam` — Barcha buyruqlar ro'yxati
"""
    web_app_url = database.get_setting("web_app_url", "").strip()
    keyboard = None
    # Telegram faqat https:// havolalarni qabul qiladi
    if web_app_url and web_app_url.lower().startswith("https://"):
        try:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 SmartTask Ilovasini Ochish", web_app=WebAppInfo(url=web_app_url))]
            ])
        except Exception as e:
            logger.warning(f"Keyboard yaratishda xatolik: {e}")

    await safe_reply(update, welcome_text, reply_markup=keyboard)


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_str = date.today().strftime("%Y-%m-%d")
    
    # Tasks summary
    stats = database.get_period_stats(today_str, today_str)
    tasks = stats["tasks"]
    total = stats["total_tasks"]
    done = stats["completed_tasks"]
    rate = stats["completion_rate"]

    # Fitness summary
    fit = database.get_fitness_summary(today_str)
    profile = fit["profile"]

    report_text = f"""📊 **{today_str} KUNLIK HISOBOT**

📌 **Vazifalar Natijasi:**
- Jami reja: {total} ta
- Bajarildi: {done} ta ({rate}%)
- Jarayonda: {total - done} ta
"""
    if tasks:
        report_text += "\n**Vazifalar:**\n"
        for t in tasks[:7]:
            status_icon = "✅" if t["status"] == "Bajarildi" else "⏳"
            time_info = f" ({t['due_time']})" if t["due_time"] else ""
            report_text += f"{status_icon} {t['title']}{time_info} [{t['priority']}]\n"

    report_text += f"""
💪 **Fitnes va Kaloriya Balansi:**
- Iste'mol qilindi: **{fit['consumed_calories']} kcal**
- Mashg'ulotda yoqildi: **{fit['burned_calories']} kcal**
- Sof kaloriya (Net): **{fit['net_calories']} kcal** / {profile['target_calories']} kcal
- Oqsil (Protein): **{fit['total_protein']}g** / {profile['target_protein_g']}g
- Ichilgan suv: **{fit['water_ml']} ml** / {profile['target_water_ml']} ml
"""
    await safe_reply(update, report_text)


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, "Haftalik chuqur tahlil tayyorlanmoqda, kuting...")
    report = ai_agent.generate_weekly_report()
    stats = report["stats"]
    
    text = f"""📈 **HAFTALIK HISOBOT ({report['start_date']} — {report['end_date']})**

- Jami vazifalar: {stats['total_tasks']} ta
- Bajarilgan: {stats['completed_tasks']} ta ({stats['completion_rate']}%)
- Kechikkanlar: {stats['overdue_tasks']} ta

💡 **AI Xulosasi:**
{report['ai_analysis'][:1200]}...
"""
    await safe_reply(update, text)


async def water_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_str = date.today().strftime("%Y-%m-%d")
    amount = 250
    if context.args:
        try:
            amount = int(context.args[0])
        except ValueError:
            amount = 250

    total = database.add_water_log(today_str, amount)
    await safe_reply(update, f"💧 +{amount}ml suv qo'shildi!\nBugungi jami: **{total} ml**")


async def food_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "Iltimos, taom nomini yozing.\nMasalan: `/taom 200gr tovuq va grechka`")
        return

    text = " ".join(context.args)
    await process_food_entry(update, text)


async def workout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "Iltimos, mashg'ulotni yozing.\nMasalan: `/mashq Zalda 45 daqiqa mashq qildim`")
        return

    text = " ".join(context.args)
    await process_workout_entry(update, text)


async def process_food_entry(update: Update, text: str):
    today_str = date.today().strftime("%Y-%m-%d")
    parsed = ai_agent.parse_food_nlp(text)
    
    saved = database.add_nutrition_log(
        date_str=today_str,
        meal_type=parsed["meal_type"],
        food_name=parsed["food_name"],
        calories=parsed["calories"],
        protein=parsed["protein"],
        carbs=parsed["carbs"],
        fat=parsed["fat"],
        weight_grams=parsed["weight_grams"]
    )
    
    fit = database.get_fitness_summary(today_str)

    msg = f"""✅ **Taomnoma saqlandi!**
🍽️ **{saved['meal_type']}:** {saved['food_name']} ({saved['weight_grams']}g)
🔥 Kaloriya: **{saved['calories']} kcal**
🥩 Oqsil (Protein): **{saved['protein']}g**
🍚 Uglevod: **{saved['carbs']}g** | 🥑 Yog': **{saved['fat']}g**

📊 Bugungi jami: **{fit['consumed_calories']} kcal** | Oqsil: **{fit['total_protein']}g**
"""
    await safe_reply(update, msg)


async def process_workout_entry(update: Update, text: str):
    today_str = date.today().strftime("%Y-%m-%d")
    profile = database.get_fitness_profile()
    parsed = ai_agent.parse_workout_nlp(text, profile.get("current_weight_kg", 75.0))

    saved = database.add_workout_log(
        date_str=today_str,
        workout_type=parsed["workout_type"],
        duration_minutes=parsed["duration_minutes"],
        calories_burned=parsed["calories_burned"],
        notes=parsed["notes"]
    )

    fit = database.get_fitness_summary(today_str)

    msg = f"""🏋️ **Mashg'ulot saqlandi!**
Turi: **{saved['workout_type']}**
Vaqti: **{saved['duration_minutes']} daqiqa**
🔥 Sarflangan kaloriya: **-{saved['calories_burned']} kcal**

📊 Bugungi sport sarfi: **-{fit['burned_calories']} kcal**
"""
    await safe_reply(update, msg)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    text_lower = text.lower()

    # Check if this is a food message
    food_triggers = ["yedim", "ichdim", "taom", "nonushta", "tushlik", "kechki ovqat", "gazak", "gr ", "gramm", "tuxum", "palov", "osh ", "tovuq"]
    workout_triggers = ["mashq", "zalda", "trenajor", "yugurdim", "kardio", "turnik", "suzdim"]

    if any(k in text_lower for k in food_triggers):
        await process_food_entry(update, text)
        return

    if any(k in text_lower for k in workout_triggers):
        await process_workout_entry(update, text)
        return

    # Otherwise, treat as task
    parsed = ai_agent.parse_task_nlp(text)
    saved = database.create_task(
        title=parsed["title"],
        description=parsed.get("description", text),
        category=parsed.get("category", "Ish"),
        priority=parsed.get("priority", "O'rta"),
        due_date=parsed.get("due_date", date.today().strftime("%Y-%m-%d")),
        due_time=parsed.get("due_time", "")
    )

    time_str = f"⏰ Vaqt: {saved['due_time']}\n" if saved['due_time'] else ""
    msg = f"""✅ **Vazifa muvaffaqiyatli qo'shildi!**
📌 Sarlavha: **{saved['title']}**
📅 Sana: **{saved['due_date']}**
{time_str}🎯 Ustuvorlik: **{saved['priority']}**
🏷️ Kategoriya: **{saved['category']}**

*Saytingizdagi vazifalar doskasida ham darhol ko'rindi!*
"""
    await safe_reply(update, msg)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("done_"):
        try:
            task_id = int(data.split("_")[1])
            task = database.get_task(task_id)
            if task:
                database.update_task(task_id, {"status": "Bajarildi"})
                await query.edit_message_text(
                    f"🎉 **Ajoyib!**\n\n📌 **\"{task['title']}\"** vazifasi muvaffaqiyatli bajarildi deb belgilandi! ✅\n*Saytingizdagi jadvalda ham darhol yangilandi.*",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Callback error: {e}")


async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_str = date.today().strftime("%Y-%m-%d")
    stats = database.get_period_stats(today_str, today_str)
    tasks = [t for t in stats["tasks"] if t["status"] != "Bajarildi"]

    if not tasks:
        await safe_reply(update, "Bugunga kutilayotgan bajarilmagan vazifalar yo'q! 🎉")
        return

    text = "🔔 **Bugungi vazifalar va bildirishnomalar vaqti:**\n\n"
    for t in tasks:
        time_info = f"⏰ {t['due_time']}" if t.get('due_time') else "⏰ Vaqt belgilanmagan"
        reminded_info = " (Eslatma yuborilgan)" if t.get('reminded') else " (Kutilmoqda)"
        text += f"▫️ **{t['title']}** — {time_info}{reminded_info}\n"

    text += "\n*Tizim har bir vazifaning vaqti kelganda sizga avtomatik eslatma yuboradi!*"
    await safe_reply(update, text)


async def kalendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vazifalar kalendarini (.ics) generatsiya qilib, foydalanuvchiga yuborish."""
    tasks = database.list_tasks(status="Ochiq")
    calendar_tasks = [t for t in tasks if t.get("due_date")]

    if not calendar_tasks:
        await safe_reply(update, "Hozircha kalendarga kiritish uchun muddatli vazifalar mavjud emas. Yangi vazifa qo'shsangiz, uni kalendaringizga ulab beraman! 📅")
        return

    ical_text = calendar_service.generate_ical_feed(calendar_tasks, "SmartTask AI Vazifalari")
    web_app_url = database.get_setting("web_app_url", "").strip()

    sub_url_info = ""
    if web_app_url and web_app_url.lower().startswith("https://"):
        feed_url = f"{web_app_url.rstrip('/')}/api/calendar/tasks.ics"
        sub_url_info = f"\n\n🔗 **Doimiy avtomatik obuna havolasi (Google Calendar / Apple Calendar):**\n`{feed_url}`\n*(Ushbu havolani kalendaringizga obuna qilsangiz, keyingi qo'shilgan vazifalar ham avtomatik sinxronlanadi!)*"

    text = f"""📅 **SmartTask AI — Kalendar Integratsiyasi va Telefon Eslatmalari**

Ushbu kalendar fayli orqali barcha vazifalaringizni telefoningiz (iPhone / Android) kalendariga ulab olishingiz mumkin.

🔔 **Afzalliklari:**
- Har bir vazifa muddati yetishidan **15 daqiqa oldin** telefoningiz qulf ekranida eslatma va ovozli signal beradi!
- Internet bo'lmagan taqdirda ham telefoningiz vazifalarni eslatib turadi.

📥 **Qanday ulanadi?**
1. Quyidagi **smarttask_tasks.ics** faylini bosing va yuklab oling.
2. Ochib, **«Barchasini qo'shish»** yoki **«Kalendarga kiritish»** tugmasini bosing.{sub_url_info}
"""
    await safe_reply(update, text)

    try:
        ics_bytes = ical_text.encode("utf-8")
        bio = io.BytesIO(ics_bytes)
        bio.name = "smarttask_tasks.ics"
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=bio,
            filename="smarttask_tasks.ics",
            caption="📅 SmartTask AI Vazifalar Kalendari (.ics) — 15 daqiqa oldingi eslatmalar bilan"
        )
    except Exception as e:
        logger.error(f"Kalendar faylini yuborishda xatolik: {e}")


async def notification_worker(application):
    logger.info("Notification worker background oqimi ishga tushdi...")
    last_morning_date = None
    last_evening_date = None
    last_water_hour = None

    while True:
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            current_time_str = now.strftime("%H:%M")
            subscribers = database.get_active_telegram_subscribers()

            if subscribers:
                # 1. Vazifalar eslatmasi (Due Tasks Reminder)
                due_tasks = database.get_due_tasks_for_reminders(current_time_str)
                for task in due_tasks:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Bajarildi deb belgilash", callback_data=f"done_{task['id']}")]
                    ])
                    desc_part = f"\n📝 Tavsif: {task['description']}" if task.get('description') else ""
                    msg = f"""🔔 **VAZIFA ESLATMASI!**

📌 **{task['title']}**
⏰ Belgilangan vaqt: **{task['due_time']}**
🎯 Ustuvorlik: **{task['priority']}**
🏷️ Kategoriya: **{task['category']}**{desc_part}

*Vazifani yakunladingizmi? Pastdagi tugmani bosing:*"""

                    for chat_id in subscribers:
                        try:
                            await application.bot.send_message(
                                chat_id=chat_id,
                                text=msg,
                                reply_markup=keyboard,
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.warning(f"Reminder yuborishda xatolik ({chat_id}): {e}")

                    database.mark_task_reminded(task['id'])

                # 2. Ertalabki reja brifingi (Har kuni soat 09:00 da)
                if now.hour == 9 and now.minute == 0 and last_morning_date != today_str:
                    last_morning_date = today_str
                    stats = database.get_period_stats(today_str, today_str)
                    tasks = stats["tasks"]
                    open_tasks = [t for t in tasks if t["status"] != "Bajarildi"]

                    briefing = f"""☀️ **XAYRLI TONG! BUGUNGI REJA BRiFiNGI** ({today_str})

Bugun sizni **{len(open_tasks)} ta** vazifa kutmoqda:
"""
                    if open_tasks:
                        for t in open_tasks[:8]:
                            time_str = f" ({t['due_time']})" if t['due_time'] else ""
                            briefing += f"▫️ {t['title']}{time_str} [{t['priority']}]\n"
                    else:
                        briefing += "Bugunga yangi vazifalar yo'q. Kuningiz maroqli o'tsin!\n"

                    briefing += "\n💧 Kunlik suv me'yori: **2500 ml**\nKuningiz unumli va omadli o'tsin! 🚀"

                    for chat_id in subscribers:
                        try:
                            await application.bot.send_message(chat_id=chat_id, text=briefing, parse_mode="Markdown")
                        except Exception as e:
                            logger.warning(f"Morning briefing error ({chat_id}): {e}")

                # 3. Kechki natijalar (Har kuni soat 21:00 da)
                if now.hour == 21 and now.minute == 0 and last_evening_date != today_str:
                    last_evening_date = today_str
                    stats = database.get_period_stats(today_str, today_str)
                    fit = database.get_fitness_summary(today_str)

                    recap = f"""🌙 **KUN YAKUNI: NATIJALAR VA HISOBOT**

📊 **Vazifalar:**
- Jami: {stats['total_tasks']} ta
- Bajarildi: {stats['completed_tasks']} ta ({stats['completion_rate']}%)
- Qolgan: {stats['total_tasks'] - stats['completed_tasks']} ta

💪 **Kaloriya va Fitnes:**
- Qabul qilingan kaloriya: {fit['consumed_calories']} kcal
- Mashqda yoqilgan: {fit['burned_calories']} kcal
- Ichilgan suv: {fit['water_ml']} ml / {fit['profile']['target_water_ml']} ml

Bugun juda yaxshi ishladingiz! Maroqli dam oling. 😴"""

                    for chat_id in subscribers:
                        try:
                            await application.bot.send_message(chat_id=chat_id, text=recap, parse_mode="Markdown")
                        except Exception as e:
                            logger.warning(f"Evening recap error ({chat_id}): {e}")

                # 4. Suv ichish eslatmasi (Kunduzi soat 11:30, 14:00, 16:30, 19:00 larda)
                if now.hour in [11, 14, 16, 19] and now.minute == 30 and last_water_hour != now.hour:
                    last_water_hour = now.hour
                    fit = database.get_fitness_summary(today_str)
                    water_msg = f"""💧 **Suv ichish vaqti!**
Tetiklashish va moddalar almashinuvini yaxshilash uchun bir stakan toza suv iching.
Bugungi jami: **{fit['water_ml']} ml** / {fit['profile']['target_water_ml']} ml

Tezkor qo'shish uchun: `/suv`"""
                    for chat_id in subscribers:
                        try:
                            await application.bot.send_message(chat_id=chat_id, text=water_msg, parse_mode="Markdown")
                        except Exception as e:
                            pass

        except Exception as loop_err:
            logger.error(f"Worker loop error: {loop_err}")

        await asyncio.sleep(25)


def main():
    database.init_db()
    token = get_bot_token()

    if not token:
        print("=" * 60)
        print("⚠️  TELEGRAM BOT TOKENI TOPILMADI!")
        print("=" * 60)
        print("1. Telegramda @BotFather ga kiring va /newbot buyrug'i bilan yangi bot oching.")
        print("2. BotFather bergan HTTP API tokenni oling.")
        print("3. Saytning 'Sozlamalar' oynasiga kiring yoki quyidagi buyruq bilan o'rnating:")
        print("   python -c \"import database; database.set_setting('telegram_bot_token', 'SIZNING_TOKENINGIZ')\"")
        print("=" * 60)
        return

    print("=" * 60)
    print("🚀 SmartTask AI Telegram Boti ishga tushirilmoqda...")
    print("=" * 60)

    async def post_init(application):
        # Background notification worker ni ishga tushirish
        asyncio.create_task(notification_worker(application))

        web_app_url = database.get_setting("web_app_url", "").strip()
        if web_app_url and web_app_url.lower().startswith("https://"):
            try:
                await application.bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text="📱 Ilova", web_app=WebAppInfo(url=web_app_url))
                )
                logger.info(f"Telegram Menu Button WebApp muvaffaqiyatli sozlandi: {web_app_url}")
            except Exception as e:
                logger.warning(f"Menu button set error: {e}")
        else:
            try:
                await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
            except Exception as e:
                logger.debug(f"Default menu button error: {e}")

    app = ApplicationBuilder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("yordam", start_command))
    app.add_handler(CommandHandler("bugun", today_command))
    app.add_handler(CommandHandler("hisobot", today_command))
    app.add_handler(CommandHandler("haftalik", weekly_command))
    app.add_handler(CommandHandler("suv", water_command))
    app.add_handler(CommandHandler("taom", food_command))
    app.add_handler(CommandHandler("mashq", workout_command))
    app.add_handler(CommandHandler("eslatma", reminder_command))
    app.add_handler(CommandHandler("kalendar", kalendar_command))
    app.add_handler(CommandHandler("calendar", kalendar_command))

    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("✅ Bot faol va bildirishnomalar tizimi ishlamoqda!")
    print("Telegramingizda botingizga /start deb yozing.")
    app.run_polling()


if __name__ == "__main__":
    main()
