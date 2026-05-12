import requests
from datetime import datetime, timedelta, timezone as dt_timezone
from django.core.cache import cache
from django.utils import timezone
import time

class MonobankService:
    BASE_URL = 'https://api.monobank.ua'
    CACHE_TIMEOUT = 60  # 1 хвилина в секундах

    def __init__(self, user=None):
        self.user = user

    def sync_transactions(self, connection, days=30, date_from=None, date_to=None):
        """Синхронізація транзакцій Монобанку з базою даних"""
        from finance.models import Transaction
        
        # Передаємо дати далі
        all_transactions = self.get_transactions(connection.access_token, days=days, date_from=date_from, date_to=date_to)
        
        added = 0
        updated = 0
        
        for t in all_transactions:
            source_id = t.get('id')
            if not source_id:
                continue
                
            amount_float = t.get('amount', 0)
            
            try:
                tx_date = datetime.fromisoformat(t.get('transaction_date'))
                # Після виправлення _format_transactions дата вже UTC-aware (+00:00).
                # Якщо з якоїсь причини naive — вважаємо UTC.
                if timezone.is_naive(tx_date):
                    tx_date = timezone.make_aware(tx_date, dt_timezone.utc)
            except Exception:
                continue
            
            existing = Transaction.objects.filter(
                user=self.user, 
                source='monobank', 
                source_id=source_id
            ).first()
            
            if existing:
                existing.description  = t.get('description', '')
                existing.counterparty = t.get('counterparty', '')
                existing.type         = t.get('type')
                existing.category_id  = t.get('category_id')
                existing.amount       = amount_float
                existing.raw_data     = t
                if not existing.connection_id:
                    existing.connection_id = connection.id
                existing.save()
                updated += 1
            else:
                Transaction.objects.create(
                    user=self.user,
                    source='monobank',
                    source_id=source_id,
                    connection_id=connection.id,
                    type=t.get('type'),
                    amount=amount_float,
                    currency=t.get('currency', 'UAH'),
                    description=t.get('description', ''),
                    counterparty=t.get('counterparty', ''),
                    transaction_date=tx_date,
                    raw_data=t
                )
                added += 1
                
        return {
            "success": True,
            "transactions_added": added,
            "transactions_updated": updated,
            "total_fetched": len(all_transactions)
        }

    @staticmethod
    def validate_token(token):
        """Перевірка валідності токена"""
        try:
            headers = {'X-Token': token}
            response = requests.get(f'{MonobankService.BASE_URL}/personal/client-info', headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def get_client_info(token):
        """Отримати інформацію про клієнта та його рахунки"""
        cache_key = f'monobank_client_{token[:20]}'
        cached_data = cache.get(cache_key)

        if cached_data:
            print('Використовуємо кеш для client_info')
            return cached_data

        headers = {'X-Token': token}
        response = requests.get(f'{MonobankService.BASE_URL}/personal/client-info', headers=headers)

        if response.status_code == 200:
            data = response.json()
            cache.set(cache_key, data, MonobankService.CACHE_TIMEOUT)
            return data
        else:
            raise Exception(f'Помилка отримання інфо: {response.text}')

    @staticmethod
    def get_transactions(token, days=30, date_from=None, date_to=None):
        """Отримати транзакції з ВСІХ рахунків за період"""
        # Динамічний ключ кешу, щоб не переплутати вибірку за дні з вибіркою за дати
        cache_date_str = f"{date_from}_{date_to}" if date_from and date_to else str(days)
        cache_key = f'monobank_transactions_{token[:20]}_{cache_date_str}'
        cached_transactions = cache.get(cache_key)

        if cached_transactions:
            print(f'Використовуємо кеш для транзакцій ({len(cached_transactions)} шт)')
            return cached_transactions

        try:
            client_info = MonobankService.get_client_info(token)
            accounts = client_info.get('accounts', [])
            own_ibans = {acc.get('iban') for acc in accounts if acc.get('iban')}

            all_transactions = []

            for idx, account in enumerate(accounts):
                account_id = account.get('id')
                try:
                    if idx > 0:
                        time.sleep(1)

                    transactions = MonobankService._get_account_transactions(
                        token, account_id, days, date_from, date_to, own_ibans
                    )
                    all_transactions.extend(transactions)
                except Exception as e:
                    print(f"Помилка для рахунку {account_id}: {str(e)}")
                    continue

            all_transactions.sort(key=lambda x: x['transaction_date'], reverse=True)

            cache.set(cache_key, all_transactions, MonobankService.CACHE_TIMEOUT)
            print(f'Збережено в кеш {len(all_transactions)} транзакцій')

            return all_transactions

        except Exception as e:
            raise Exception(f'Помилка отримання транзакцій: {str(e)}')

    @staticmethod
    def _get_account_transactions(token, account_id, days=30, date_from=None, date_to=None, own_ibans=None):
        """Отримати транзакції для конкретного рахунку з розбивкою по 31 дню"""
        cache_date_str = f"{date_from}_{date_to}" if date_from and date_to else str(days)
        cache_key = f'monobank_account_{token[:20]}_{account_id}_{cache_date_str}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        headers = {'X-Token': token}
        
        # Логіка визначення стартової та кінцевої дати
        if date_from and date_to:
            start_date = timezone.make_aware(datetime.combine(date_from, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(date_to, datetime.max.time()))
            # Відсікаємо майбутнє
            if end_date > timezone.now():
                end_date = timezone.now()
        else:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
        
        all_raw_transactions = []
        current_end = end_date
        
        while current_end > start_date:
            current_start = max(start_date, current_end - timedelta(days=31))
            
            from_time = int(current_start.timestamp())
            to_time = int(current_end.timestamp())

            url = f'{MonobankService.BASE_URL}/personal/statement/{account_id}/{from_time}/{to_time}'
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                chunk = response.json()
                all_raw_transactions.extend(chunk)
            elif response.status_code == 429:
                print(f'Too many requests для рахунку {account_id}, перериваємо (сервер не зависатиме)')
                break
            else:
                print(f'Помилка {response.status_code} для рахунку {account_id}: {response.text}')
                break
                
            current_end = current_start
            time.sleep(0.2)

        formatted = MonobankService._format_transactions(all_raw_transactions, account_id, own_ibans)
        cache.set(cache_key, formatted, MonobankService.CACHE_TIMEOUT)
        return formatted

    @staticmethod
    def _format_transactions(transactions, account_id=None, own_ibans=None):
        """
        Форматувати транзакції в єдиний формат.
        Внутрішній переказ між власними рахунками визначається за counterIban:
        якщо IBAN контрагента збігається з одним із власних рахунків — це 'transfer'.
        """
        own_ibans = own_ibans or set()
        formatted = []

        for t in transactions:
            amount = t.get('amount', 0) / 100

            # Визначаємо тип: перевіряємо counterIban проти власних рахунків
            counter_iban = t.get('counterIban', '')
            if counter_iban and counter_iban in own_ibans:
                # Це переказ між власними рахунками (наприклад, до накопичувального)
                trans_type = 'transfer'
                amount = abs(amount)
            elif amount > 0:
                trans_type = 'income'
            else:
                trans_type = 'expense'
                amount = abs(amount)

            description = t.get('description', 'Без опису')
            counterparty = description.split('\n')[0] if '\n' in description else description

            formatted.append({
                'id': t.get('id'),
                'account_id': account_id,
                'source': 'monobank',
                'type': trans_type,
                'amount': amount,
                'currency': 'UAH',
                'description': description,
                'counterparty': counterparty,
                'mcc': t.get('mcc'),
                # Конвертуємо Unix-timestamp у UTC (без локального зміщення сервера)
                'transaction_date': datetime.fromtimestamp(t.get('time'), tz=dt_timezone.utc).isoformat(),
                'raw_data': t
            })
        return formatted
