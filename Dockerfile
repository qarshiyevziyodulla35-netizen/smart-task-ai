FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Tizim paketlari
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha loyiha fayllarini nusxalash
COPY . .

# Ma'lumotlar saqlanadigan papka
RUN mkdir -p /app/data

EXPOSE 8000
VOLUME ["/app/data"]

# Bazani ishga tushirish, Telegram botni orqa fonda va veb-serverni asosiy jarayon sifatida yurgizish
CMD ["sh", "-c", "python -c 'from backend.database import init_db; init_db()' && (python telegram_bot.py &) && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
