import os
import sys
import time
import threading
from django.apps import AppConfig


def start_hourly_sync_thread():
    from finance.tasks import sync_all_monobank, sync_all_exchanges
    from django.db import connections

    def sync_loop():
        # Затримка перед першим запуском, щоб сервер встиг завантажитись
        time.sleep(30)
        while True:
            try:
                print("[Threading AutoSync] Starting hourly sync...")
                sync_all_monobank()
                sync_all_exchanges()
                print("[Threading AutoSync] Completed hourly sync.")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[Threading AutoSync] Global Error: {e}")
            finally:
                # Обов'язково закриваємо з'єднання після завершення циклу операцій 
                # (інакше з'єднання можуть зависнути або виникне помилка 'MySQL server has gone away')
                connections.close_all()
            
            # Чекаємо 1 годину (3600 секунд) до наступної синхронізації
            time.sleep(3600)

    thread = threading.Thread(target=sync_loop, daemon=True, name="HourlySyncThread")
    thread.start()


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'

    def ready(self):
        # Запобігаємо подвійному запуску фонового потоку при використанні Django runserver
        if os.environ.get('RUN_MAIN') == 'true' or 'runserver' not in sys.argv:
            start_hourly_sync_thread()
