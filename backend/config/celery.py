"""
Celery Configuration for Background Tasks
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('diploma_backend')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    # Синхронізація Monobank кожні 2 години
    'sync-monobank-every-2-hours': {
        'task': 'finance.tasks.sync_all_monobank',
        'schedule': crontab(minute=0, hour='*/2'),
    },
    # Синхронізація ПУМБ кожні 3 години
    'sync-pumb-every-3-hours': {
        'task': 'finance.tasks.sync_all_pumb',
        'schedule': crontab(minute=0, hour='*/3'),
    },
    # Синхронізація бірж кожні 4 години
    'sync-exchanges-every-4-hours': {
        'task': 'finance.tasks.sync_all_exchanges',
        'schedule': crontab(minute=0, hour='*/4'),
    },
    # Очищення старих логів синхронізації раз на день
    'cleanup-old-logs-daily': {
        'task': 'finance.tasks.cleanup_old_sync_logs',
        'schedule': crontab(minute=0, hour=3),  # Кожного дня о 3:00
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Kiev',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
