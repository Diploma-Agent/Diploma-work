import requests
from datetime import datetime, timedelta
from django.utils import timezone
from finance.models import BankConnection, Transaction, TransactionCategory, SyncLog


class MonobankService:
    """Сервіс для роботи з Monobank API"""
    
    BASE_URL = "https://api.monobank.ua"
    
    def __init__(self, user, token=None):
        self.user = user
        self.token = token
        
    def get_client_info(self):
        """Отримати інформацію про клієнта"""
        headers = {'X-Token': self.token}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/personal/client-info",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Помилка отримання інформації: {str(e)}")
    
    def get_statements(self, account_id, from_time=None, to_time=None):
        """
        Отримати виписку по рахунку
        
        Args:
            account_id: ID рахунку
            from_time: Початок періоду (Unix timestamp)
            to_time: Кінець періоду (Unix timestamp)
        """
        if from_time is None:
            # За замовчуванням - останні 30 днів
            from_time = int((timezone.now() - timedelta(days=30)).timestamp())
        
        if to_time is None:
            to_time = int(timezone.now().timestamp())
            
        headers = {'X-Token': self.token}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/personal/statement/{account_id}/{from_time}/{to_time}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Помилка отримання виписки: {str(e)}")
    
    def sync_transactions(self, bank_connection, days=30):
        """
        Синхронізувати транзакції з Monobank
        
        Args:
            bank_connection: Об'єкт BankConnection
            days: Кількість днів для синхронізації
        """
        sync_log = SyncLog.objects.create(
            user=self.user,
            source='monobank',
            status='partial'
        )
        
        try:
            self.token = bank_connection.access_token
            
            # Отримуємо інформацію про клієнта
            client_info = self.get_client_info()
            
            transactions_added = 0
            transactions_updated = 0
            
            # Проходимо по всіх рахунках
            for account in client_info.get('accounts', []):
                account_id = account['id']
                
                # Розраховуємо часові рамки
                to_time = int(timezone.now().timestamp())
                from_time = int((timezone.now() - timedelta(days=days)).timestamp())
                
                # Отримуємо виписку
                statements = self.get_statements(account_id, from_time=from_time, to_time=to_time)
                
                for stmt in statements:
                    transaction_id = stmt['id']
                    
                    # Визначаємо тип транзакції
                    amount = stmt['amount'] / 100  # Monobank повертає в копійках
                    trans_type = 'income' if amount > 0 else 'expense'
                    
                    # Класифікуємо транзакцію
                    category = self._classify_transaction(stmt)
                    
                    # Створюємо або оновлюємо транзакцію
                    transaction, created = Transaction.objects.update_or_create(
                        source='monobank',
                        source_id=transaction_id,
                        defaults={
                            'user': self.user,
                            'type': trans_type,
                            'category': category,
                            'amount': abs(amount),
                            'currency': self._get_currency_code(stmt.get('currencyCode')),
                            'description': stmt.get('description', ''),
                            'counterparty': stmt.get('counterparty', {}).get('name', ''),
                            'transaction_date': timezone.make_aware(
                                datetime.fromtimestamp(stmt['time'])
                            ),
                            'raw_data': stmt
                        }
                    )
                    
                    if created:
                        transactions_added += 1
                    else:
                        transactions_updated += 1
            
            # Оновлюємо статус підключення
            bank_connection.last_sync = timezone.now()
            bank_connection.status = 'active'
            bank_connection.error_message = None
            bank_connection.save()
            
            # Оновлюємо лог
            sync_log.status = 'success'
            sync_log.transactions_added = transactions_added
            sync_log.transactions_updated = transactions_updated
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            return {
                'success': True,
                'transactions_added': transactions_added,
                'transactions_updated': transactions_updated
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            bank_connection.status = 'error'
            bank_connection.error_message = str(e)
            bank_connection.save()
            
            raise
    
    def _classify_transaction(self, statement):
        """Класифікувати транзакцію за MCC кодом та описом"""
        mcc = statement.get('mcc')
        description = statement.get('description', '').lower()
        
        # Категорії за MCC кодами
        mcc_categories = {
            # Продукти
            (5411, 5412, 5499): 'Продукти',
            # Ресторани
            (5812, 5813, 5814): 'Ресторани',
            # Транспорт
            (4111, 4112, 4121, 4131, 4784, 4789): 'Транспорт',
            # Медицина
            (8011, 8021, 8031, 8041, 8042, 8043, 8049, 8050, 8062, 8071, 8099): 'Медицина',
            # Розваги
            (7832, 7841, 7911, 7922, 7929, 7932, 7933, 7991, 7992, 7993, 7994, 7995, 7996, 7997, 7998, 7999): 'Розваги',
            # Одяг
            (5611, 5621, 5631, 5641, 5651, 5661, 5691, 5699): 'Одяг',
            # Комунальні послуги
            (4900,): 'Комунальні послуги',
        }
        
        category_name = 'Інше'
        
        if mcc:
            for mcc_codes, cat_name in mcc_categories.items():
                if mcc in mcc_codes:
                    category_name = cat_name
                    break
        
        # Додаткова класифікація за описом
        if 'atm' in description or 'банкомат' in description:
            category_name = 'Зняття готівки'
        elif 'transfer' in description or 'переказ' in description:
            category_name = 'Перекази'
        
        # Отримуємо або створюємо категорію
        category, _ = TransactionCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'type': 'expense' if statement.get('amount', 0) < 0 else 'income',
                'is_system': True
            }
        )
        
        return category
    
    def _get_currency_code(self, currency_code):
        """Конвертувати код валюти з числового у текстовий"""
        currency_map = {
            980: 'UAH',
            840: 'USD',
            978: 'EUR',
            826: 'GBP',
        }
        return currency_map.get(currency_code, 'UAH')
    
    @staticmethod
    def validate_token(token):
        """Перевірити валідність токена"""
        headers = {'X-Token': token}
        
        try:
            response = requests.get(
                f"{MonobankService.BASE_URL}/personal/client-info",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
