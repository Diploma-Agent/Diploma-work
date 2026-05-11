#!/bin/bash

# Функція для завершення процесів при виході
cleanup() {
    echo "Zupynka serveriv..."
    kill $BACKEND_PID
    kill $CELERY_WORKER_PID
    kill $CELERY_BEAT_PID
    kill $FRONTEND_PID
    exit
}

# Перехоплення SIGINT (Ctrl+C)
trap cleanup SIGINT

# Запуск Backend
echo "Zapusk Django Backend..."
cd backend
# Спроба активації віртуального оточення (якщо є)
if [ -d "venv" ]; then
    source venv/Scripts/activate
elif [ -d ".venv" ]; then
    source .venv/Scripts/activate
fi

python manage.py runserver &
BACKEND_PID=$!

echo "Zapusk Celery Worker..."
celery -A config worker -l info &
CELERY_WORKER_PID=$!

echo "Zapusk Celery Beat..."
celery -A config beat -l info &
CELERY_BEAT_PID=$!

# Запуск Frontend
echo "Zapusk React Frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Очікування
wait