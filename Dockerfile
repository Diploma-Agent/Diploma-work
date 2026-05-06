# ── Production image — FinanceApp Backend ─────────────────────────────────────
# Dockerfile знаходиться в корені репо (Render шукає саме тут за замовчуванням).
# Build context = корінь репозиторію.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Залежності — окремий шар для кешування
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код бекенду
COPY backend/ .

# Права на entrypoint
RUN chmod +x /app/entrypoint.sh

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
