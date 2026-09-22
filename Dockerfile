FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Tizim paketlari
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Talab qilinadigan kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodlari
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY telegram_bot.py .
COPY entrypoint.sh .

# Kirish skriptiga ijro ruxsatini berish
RUN chmod +x entrypoint.sh

# Doimiy ma'lumotlar saqlanadigan papka
RUN mkdir -p /app/data

EXPOSE 8000

VOLUME ["/app/data"]

CMD ["/app/entrypoint.sh"]
