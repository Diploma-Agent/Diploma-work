import requests
from datetime import datetime, timedelta
from django.core.cache import cache
import time


class MonobankService:
    BASE_URL = 'https://api.monobank.ua'
    CACHE_TIMEOUT = 60  # 1 хвилина в секундах
    
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
        # Спробуємо отримати з кешу
        cache_key = f'monobank_client_{token[:20]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            print(f'Використовуємо кеш для client_info')
            return cached_data
        
        headers = {'X-Token': token}
        response = requests.get(f'{MonobankService.BASE_URL}/personal/client-info', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # Кешуємо на 10 хвилин
            cache.set(cache_key, data, MonobankService.CACHE_TIMEOUT)
            return data
        else:
            raise Exception(f'Помилка отримання інфо: {response.text}')
    
    @staticmethod
    def get_transactions(token, days=30):
        """Отримати транзакції з ВСІХ рахунків за останні N днів"""
        # Спробуємо отримати з кешу
        cache_key = f'monobank_transactions_{token[:20]}_{days}'
        cached_transactions = cache.get(cache_key)
        
        if cached_transactions:
            print(f'Використовуємо кеш для транзакцій ({len(cached_transactions)} шт)')
            return cached_transactions
        
        try:
            # Спочатку отримуємо інфо про клієнта та рахунки
            client_info = MonobankService.get_client_info(token)
            accounts = client_info.get('accounts', [])
            
            all_transactions = []
            
            # Проходимось по кожному рахунку
            for idx, account in enumerate(accounts):
                account_id = account.get('id')
                
                try:
                    # Затримка між запитами для уникнення rate limit
                    if idx > 0:
                        time.sleep(1)  # 1 секунда між запитами
                    
                    # Отримуємо транзакції для кожного рахунку
                    transactions = MonobankService._get_account_transactions(
                        token, 
                        account_id, 
                        days
                    )
                    all_transactions.extend(transactions)
                except Exception as e:
                    print(f"Помилка для рахунку {account_id}: {str(e)}")
                    continue
            
            # Сортуємо по даті
            all_transactions.sort(key=lambda x: x['transaction_date'], reverse=True)
            
            # Кешуємо результат на 10 хвилин
            cache.set(cache_key, all_transactions, MonobankService.CACHE_TIMEOUT)
            print(f'Збережено в кеш {len(all_transactions)} транзакцій')
            
            return all_transactions
            
        except Exception as e:
            raise Exception(f'Помилка отримання транзакцій: {str(e)}')
    
    @staticmethod
    def _get_account_transactions(token, account_id, days=30):
        """Отримати транзакції для конкретного рахунку"""
        cache_key = f'monobank_account_{token[:20]}_{account_id}_{days}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        headers = {'X-Token': token}
        from_time = int((datetime.now() - timedelta(days=days)).timestamp())
        to_time = int(datetime.now().timestamp())

        url = f'{MonobankService.BASE_URL}/personal/statement/{account_id}/{from_time}/{to_time}'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            transactions = response.json()
            # Передаємо account_id щоб зберегти в транзакції
            formatted = MonobankService._format_transactions(transactions, account_id)
            cache.set(cache_key, formatted, MonobankService.CACHE_TIMEOUT)
            return formatted
        elif response.status_code == 429:
            print(f'Too many requests для рахунку {account_id}')
            return []
        else:
            print(f'Помилка {response.status_code} для рахунку {account_id}: {response.text}')
            return []

    @staticmethod
    def _format_transactions(transactions, account_id=None):
        """Форматувати транзакції в єдиний формат"""
        formatted = []
        for t in transactions:
            amount = t.get('amount', 0) / 100
            if amount > 0:
                trans_type = 'income'
            else:
                trans_type = 'expense'
                amount = abs(amount)

            description = t.get('description', 'Без опису')
            counterparty = description.split('\n')[0] if '\n' in description else description

            formatted.append({
                'id': t.get('id'),
                'account_id': account_id,          # зберігаємо account_id
                'source': 'monobank',
                'type': trans_type,
                'amount': amount,
                'currency': 'UAH',
                'description': description,
                'counterparty': counterparty,
                'transaction_date': datetime.fromtimestamp(t.get('time')).isoformat(),
                'raw_data': t
            })
        return formatted
