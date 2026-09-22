#!/bin/bash
set -e

echo "=========================================="
echo "🚀 SmartTask AI Tizimi Ishga Tushmoqda..."
echo "=========================================="

mkdir -p /app/data

# FastAPI Veb-serverini orqa fonda ishga tushirish
echo "🌐 FastAPI veb-serveri ishga tushirilmoqda (Port: ${PORT:-8000})..."
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} &
WEB_PID=$!

# Telegram botni orqa fonda ishga tushirish
echo "🤖 Telegram Bot ishga tushirilmoqda..."
python telegram_bot.py &
BOT_PID=$!

# Xavfsiz to'xtatish signallari (SIGTERM, SIGINT)
cleanup() {
    echo "⚠️ Tizim to'xtatilmoqda..."
    kill -TERM "$WEB_PID" 2>/dev/null || true
    kill -TERM "$BOT_PID" 2>/dev/null || true
    wait "$WEB_PID" 2>/dev/null || true
    wait "$BOT_PID" 2>/dev/null || true
    echo "✅ Tizim to'liq to'xtatildi."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Asosiy jarayonlarni kuzatib turish
wait -n "$WEB_PID" "$BOT_PID"
cleanup
