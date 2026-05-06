#!/bin/sh
set -e

# ── Google Service Account credentials ──────────────────────────────────────
# На Render передаємо JSON як base64-рядок через змінну середовища.
# Щоб отримати значення локально:
#   base64 -i diploma-488920-06ce8ed2bfbc.json | tr -d '\n'
# Результат вставляємо в Render → Environment → GOOGLE_CREDENTIALS_B64
if [ -n "$GOOGLE_CREDENTIALS_B64" ]; then
    echo "$GOOGLE_CREDENTIALS_B64" | base64 -d > /tmp/google_credentials.json
    export GOOGLE_CREDENTIALS=/tmp/google_credentials.json
    echo "[entrypoint] Google credentials decoded → /tmp/google_credentials.json"
fi

# ── Django startup ───────────────────────────────────────────────────────────
echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Starting: $@"
exec "$@"
