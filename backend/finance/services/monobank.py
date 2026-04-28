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
    def get_transactions(token, days=30):
        """Отримати транзакції з ВСІХ рахунків за останні N днів"""
        cache_key = f'monobank_transactions_{token[:20]}_{days}'
        cached_transactions = cache.get(cache_key)

        if cached_transactions:
            print(f'Використовуємо кеш для транзакцій ({len(cached_transactions)} шт)')
            return cached_transactions

        try:
            client_info = MonobankService.get_client_info(token)
            accounts = client_info.get('accounts', [])

            # Збираємо всі IBAN власних рахунків для визначення внутрішніх переказів
            own_ibans = {acc.get('iban') for acc in accounts if acc.get('iban')}

            all_transactions = []

            for idx, account in enumerate(accounts):
                account_id = account.get('id')

                try:
                    if idx > 0:
                        time.sleep(1)

                    transactions = MonobankService._get_account_transactions(
                        token, account_id, days, own_ibans
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
    def _get_account_transactions(token, account_id, days=30, own_ibans=None):
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
            formatted = MonobankService._format_transactions(transactions, account_id, own_ibans)
            cache.set(cache_key, formatted, MonobankService.CACHE_TIMEOUT)
            return formatted
        elif response.status_code == 429:
            print(f'Too many requests для рахунку {account_id}')
            return []
        else:
            print(f'Помилка {response.status_code} для рахунку {account_id}: {response.text}')
            return []

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
                'transaction_date': datetime.fromtimestamp(t.get('time')).isoformat(),
                'raw_data': t
            })
        return formatted
