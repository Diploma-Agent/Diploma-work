# Запуск Backend у новому вікні
Write-Host "Starting Backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python manage.py runserver"

# Запуск Celery Worker у новому вікні (для фонових завдань на Windows використовуємо --pool=solo)
Write-Host "Starting Celery Worker..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; celery -A config worker --pool=solo -l info"

# Запуск Celery Beat у новому вікні (для планування завдань за розкладом)
Write-Host "Starting Celery Beat..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; celery -A config beat -l info"

# Запуск Frontend у новому вікні
Write-Host "Starting Frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"