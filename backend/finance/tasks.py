"""
Celery Background Tasks
"""
from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from finance.models import BankConnection, CryptoExchange, SyncLog
from finance.services.monobank import MonobankService
from finance.services.binance import BinanceService
from finance.services.bybit import BybitService
from finance.services.okx import OKXService

User = get_user_model()


# ── Погодинне авто-оновлення Monobank (останні 2 дні) ──────────────────────
@shared_task(name='finance.tasks.sync_all_monobank')
def sync_all_monobank():
    """Авто-синхронізація всіх активних Monobank (запускається щогодини)"""
    connections = BankConnection.objects.filter(bank_name='monobank', status='active')
    synced, failed = 0, 0
    for connection in connections:
        try:
            service = MonobankService(connection.user)
            service.sync_transactions(connection, days=2)
            synced += 1
        except Exception as e:
            failed += 1
            print(f"[AutoSync] Monobank user={connection.user.id}: {e}")
    return {'synced': synced, 'failed': failed, 'total': connections.count()}


# ── Погодинне авто-оновлення бірж (останні 2 дні) ──────────────────────────
@shared_task(name='finance.tasks.sync_all_exchanges')
def sync_all_exchanges():
    """Авто-синхронізація всіх активних бірж (запускається щогодини)"""
    exchanges = CryptoExchange.objects.filter(status='active')
    synced, failed = 0, 0
    for exchange in exchanges:
        try:
            if exchange.exchange_name == 'binance':
                service = BinanceService(exchange.api_key, exchange.api_secret)
            elif exchange.exchange_name == 'bybit':
                service = BybitService(exchange.api_key, exchange.api_secret)
            elif exchange.exchange_name == 'okx':
                service = OKXService(exchange.api_key, exchange.api_secret, exchange.api_passphrase)
            else:
                continue
            service.sync_transactions(exchange, days=2)
            synced += 1
        except Exception as e:
            failed += 1
            print(f"[AutoSync] {exchange.exchange_name} user={exchange.user.id}: {e}")
    return {'synced': synced, 'failed': failed, 'total': exchanges.count()}


# ── Перший імпорт після додавання (90 днів = 3 місяці) ─────────────────────
@shared_task(name='finance.tasks.sync_user_connection')
def sync_user_connection(user_id, source, connection_id, days=None, date_from=None, date_to=None):
    """Синхронізація конкретного підключення.
    При першому додаванні — 90 днів (3 місяці).
    При ручному sync — може передаватись інший days або date_from/date_to.
    """
    try:
        user = User.objects.get(id=user_id)

        # Конвертуємо рядки в date, якщо вони прийшли від Celery у вигляді рядків
        if isinstance(date_from, str):
            date_from = datetime.fromisoformat(date_from).date()
        if isinstance(date_to, str):
            date_to = datetime.fromisoformat(date_to).date()

        if source == 'monobank':
            connection = BankConnection.objects.get(id=connection_id, user=user)
            service = MonobankService(user)
            return service.sync_transactions(connection, days=days, date_from=date_from, date_to=date_to)

        elif source in ['binance', 'bybit', 'okx']:
            exchange = CryptoExchange.objects.get(id=connection_id, user=user)
            if source == 'binance':
                service = BinanceService(exchange.api_key, exchange.api_secret)
            elif source == 'bybit':
                service = BybitService(exchange.api_key, exchange.api_secret)
            else:
                service = OKXService(exchange.api_key, exchange.api_secret, exchange.api_passphrase)
            return service.sync_transactions(exchange, days=days)

    except Exception as e:
        return {'error': str(e)}


# ── Ручна синхронізація (викликається користувачем) ────────────────────────
@shared_task(name='finance.tasks.manual_sync_user_connection')
def manual_sync_user_connection(user_id, source, connection_id):
    """Ручний sync: синхронізує останні 30 днів"""
    return sync_user_connection(user_id, source, connection_id, days=30)


# ── Очищення старих логів ───────────────────────────────────────────────────
@shared_task(name='finance.tasks.cleanup_old_sync_logs')
def cleanup_old_sync_logs(days=60):
    """Видалення логів синхронізації старших за 60 днів"""
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = SyncLog.objects.filter(started_at__lt=cutoff_date).delete()
    return {'deleted': deleted_count}


@shared_task(name='finance.tasks.delete_transactions_background')
def delete_transactions_background(user_id, source, connection_id):
    """Видаляє транзакції у фоні, щоб не блокувати UI користувачу"""
    from finance.models import Transaction
    
    # Видаляємо всі транзакції для цього підключення (банку чи біржі)
    deleted_count, _ = Transaction.objects.filter(
        user_id=user_id, 
        source=source, 
        connection_id=connection_id
    ).delete()
    
    return {'deleted_transactions': deleted_count}
