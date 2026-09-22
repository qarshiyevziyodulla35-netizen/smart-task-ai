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

# Barcha fayllarni konteynerga nusxalash
COPY . .

# Papkalarni avtomatik to'g'rilash va joylashtirish
RUN mkdir -p /app/backend /app/frontend /app/data && \
    cp main.py database.py ai_agent.py calendar_service.py /app/backend/ 2>/dev/null || true && \
    touch /app/backend/__init__.py && \
    cp index.html app.js /app/frontend/ 2>/dev/null || true && \
    (cp styles.css /app/frontend/ 2>/dev/null || true) && \
    sed -i 's/wait -n "\$WEB_PID" "\$BOT_PID"/wait \$WEB_PID/g' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

EXPOSE 8000

VOLUME ["/app/data"]

CMD ["/app/entrypoint.sh"]
