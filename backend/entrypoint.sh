#!/bin/sh
set -e

# ── Google Service Account credentials ──────────────────────────────────────
# Render не підтримує монтування файлів — передаємо JSON у вигляді base64.
#
# Як отримати значення для Render Dashboard → Environment:
#   macOS:  base64 -i backend/diploma-*.json | tr -d '\n'
#   Linux:  base64 -w 0 backend/diploma-*.json
#
# Python-декодування стійкіше за shell base64:
#   - ігнорує зайві пробіли та переноси рядка
#   - коректно обробляє padding
# ─────────────────────────────────────────────────────────────────────────────
if [ -n "$GOOGLE_CREDENTIALS_B64" ]; then
    python3 - <<'PYEOF'
import base64, os, sys

raw = os.environ.get("GOOGLE_CREDENTIALS_B64", "")
# Прибираємо пробіли та переноси рядка (macOS base64 додає \n кожні 76 символів)
raw = raw.strip().replace("\n", "").replace("\r", "").replace(" ", "")

if not raw:
    print("[entrypoint] GOOGLE_CREDENTIALS_B64 is empty — skipping", flush=True)
    sys.exit(0)

try:
    # Додаємо padding якщо потрібно
    padding = (4 - len(raw) % 4) % 4
    data = base64.b64decode(raw + "=" * padding)
    with open("/tmp/google_credentials.json", "wb") as f:
        f.write(data)
    print("[entrypoint] Google credentials decoded → /tmp/google_credentials.json", flush=True)
except Exception as e:
    print(f"[entrypoint] ERROR: Cannot decode GOOGLE_CREDENTIALS_B64: {e}", flush=True)
    sys.exit(1)
PYEOF
    export GOOGLE_CREDENTIALS=/tmp/google_credentials.json
fi

# ── Django startup ───────────────────────────────────────────────────────────
# Для Celery worker/beat — пропускаємо migrate та collectstatic:
# вони вже виконались у web-сервісі, а worker не потребує статики.
case "$1" in
    celery)
        echo "[entrypoint] Celery mode — skipping migrate & collectstatic"
        ;;
    *)
        echo "[entrypoint] Running migrations..."
        python manage.py migrate --noinput

        echo "[entrypoint] Collecting static files..."
        python manage.py collectstatic --noinput --clear
        ;;
esac

echo "[entrypoint] Starting: $*"
exec "$@"
