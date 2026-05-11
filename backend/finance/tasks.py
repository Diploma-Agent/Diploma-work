"""
Celery Background Tasks
"""
from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from finance.models import BankConnection, CryptoExchange, SyncLog
from finance.services.monobank import MonobankService
from finance.services.pumb import PUMBService
from finance.services.binance import BinanceService
from finance.services.bybit import BybitService
from finance.services.okx import OKXService

User = get_user_model()


@shared_task(name='finance.tasks.sync_all_monobank')
def sync_all_monobank():
    """Синхронізація всіх підключень Monobank"""
    connections = BankConnection.objects.filter(
        bank_name='monobank',
        status='active'
    )
    
    synced_count = 0
    failed_count = 0
    
    for connection in connections:
        try:
            service = MonobankService(connection.user)
            service.sync_transactions(connection, days=7)
            synced_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to sync Monobank for user {connection.user.id}: {str(e)}")
    
    return {
        'synced': synced_count,
        'failed': failed_count,
        'total': connections.count()
    }


@shared_task(name='finance.tasks.sync_all_pumb')
def sync_all_pumb():
    """Синхронізація всіх підключень ПУМБ"""
    connections = BankConnection.objects.filter(
        bank_name='pumb',
        status='active'
    )
    
    synced_count = 0
    failed_count = 0
    
    for connection in connections:
        try:
            service = PUMBService(connection.access_token)
            service.sync_transactions(connection, days=7)
            synced_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to sync PUMB for user {connection.user.id}: {str(e)}")
    
    return {
        'synced': synced_count,
        'failed': failed_count,
        'total': connections.count()
    }


@shared_task(name='finance.tasks.sync_all_exchanges')
def sync_all_exchanges():
    """Синхронізація всіх підключень до бірж"""
    exchanges = CryptoExchange.objects.filter(status='active')
    
    synced_count = 0
    failed_count = 0
    
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
            
            service.sync_transactions(exchange, days=7)
            synced_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to sync {exchange.exchange_name} for user {exchange.user.id}: {str(e)}")
    
    return {
        'synced': synced_count,
        'failed': failed_count,
        'total': exchanges.count()
    }


@shared_task(name='finance.tasks.sync_user_connection')
def sync_user_connection(user_id, source, connection_id):
    """Синхронізація конкретного підключення користувача"""
    try:
        user = User.objects.get(id=user_id)
        
        if source in ['monobank', 'pumb']:
            connection = BankConnection.objects.get(id=connection_id, user=user)
            
            if source == 'monobank':
                service = MonobankService(user)
            else:
                service = PUMBService(connection.access_token)
            
            result = service.sync_transactions(connection, days=30)
            return result
        
        elif source in ['binance', 'bybit', 'okx']:
            exchange = CryptoExchange.objects.get(id=connection_id, user=user)
            
            if source == 'binance':
                service = BinanceService(exchange.api_key, exchange.api_secret)
            elif source == 'bybit':
                service = BybitService(exchange.api_key, exchange.api_secret)
            else:
                service = OKXService(exchange.api_key, exchange.api_secret, exchange.api_passphrase)
            
            result = service.sync_transactions(exchange, days=30)
            return result
        
    except Exception as e:
        return {'error': str(e)}


@shared_task(name='finance.tasks.cleanup_old_sync_logs')
def cleanup_old_sync_logs(days=30):
    """Видалення старих логів синхронізації"""
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_count = SyncLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    return {
        'deleted': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task(name='finance.tasks.refresh_pumb_tokens')
def refresh_pumb_tokens():
    """Оновлення токенів ПУМБ"""
    from decouple import config
    
    connections = BankConnection.objects.filter(
        bank_name='pumb',
        status='active'
    )
    
    refreshed_count = 0
    failed_count = 0
    
    client_id = config('PUMB_CLIENT_ID', default='')
    client_secret = config('PUMB_CLIENT_SECRET', default='')
    
    if not client_id or not client_secret:
        return {'error': 'PUMB credentials not configured'}
    
    for connection in connections:
        try:
            if connection.refresh_token:
                # Оновлюємо access token
                token_data = PUMBService.refresh_access_token(
                    connection.refresh_token,
                    client_id,
                    client_secret
                )
                
                connection.access_token = token_data.get('access_token')
                if 'refresh_token' in token_data:
                    connection.refresh_token = token_data.get('refresh_token')
                connection.save()
                
                refreshed_count += 1
        except Exception as e:
            failed_count += 1
            connection.status = 'error'
            connection.save()
            print(f"Failed to refresh PUMB token for user {connection.user.id}: {str(e)}")
    
    return {
        'refreshed': refreshed_count,
        'failed': failed_count,
        'total': connections.count()
    }
