# ── Stage: production image ──────────────────────────────────────────────────
FROM python:3.11-slim

# Системні залежності
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Встановлюємо залежності окремим шаром (кешується при змінах коду)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код (крім виключень з .dockerignore)
COPY . .

# Права на entrypoint
RUN chmod +x /app/entrypoint.sh

# Порт Gunicorn
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

# Web service: gunicorn
# Celery worker: перевизначається через dockerCommand у render.yaml
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
