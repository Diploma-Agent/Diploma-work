# ── Production image — FinanceApp (Backend + Frontend in one container) ────────
FROM python:3.11-slim

# gcc для Python-пакетів + Node.js 20 для збірки React
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python залежності ──────────────────────────────────────────────────────────
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Збірка React фронтенду ─────────────────────────────────────────────────────
# VITE_API_BASE_URL не вказуємо — фронтенд використовує відносні шляхи /api/...
COPY frontend/ /tmp/frontend/
RUN cd /tmp/frontend && npm install --legacy-peer-deps && npm run build

# ── Код бекенду ───────────────────────────────────────────────────────────────
COPY backend/ .

# Переносимо зібраний фронтенд туди, де Django/WhiteNoise зможе роздавати його
RUN cp -r /tmp/frontend/dist /app/frontend_dist && rm -rf /tmp/frontend

# Права на entrypoint
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

# gunicorn запускає Django, який роздає і API, і React SPA
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
