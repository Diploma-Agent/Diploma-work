"""
ПУМБ Bank OAuth2 Integration Service
https://developer.pumb.ua/
"""
import requests
from datetime import datetime, timedelta
from django.conf import settings
from finance.models import Transaction, TransactionCategory, SyncLog


class PUMBService:
    """Service for PUMB Bank OAuth2 API integration"""
    
    BASE_URL = "https://api.pumb.ua"
    AUTH_URL = "https://auth.pumb.ua"
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def get_authorization_url(client_id, redirect_uri, state):
        """Generate OAuth2 authorization URL"""
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': 'account_info transactions'
        }
        url = f"{PUMBService.AUTH_URL}/oauth/authorize"
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{url}?{query_string}"
    
    @staticmethod
    def exchange_code_for_token(code, client_id, client_secret, redirect_uri):
        """Exchange authorization code for access token"""
        url = f"{PUMBService.AUTH_URL}/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to exchange code: {str(e)}")
    
    @staticmethod
    def refresh_access_token(refresh_token, client_id, client_secret):
        """Refresh access token using refresh token"""
        url = f"{PUMBService.AUTH_URL}/oauth/token"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to refresh token: {str(e)}")
    
    def get_accounts(self):
        """Get list of user's bank accounts"""
        url = f"{self.BASE_URL}/api/v1/accounts"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get accounts: {str(e)}")
    
    def get_transactions(self, account_id, from_date, to_date):
        """Get transactions for specific account"""
        url = f"{self.BASE_URL}/api/v1/accounts/{account_id}/transactions"
        params = {
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get transactions: {str(e)}")
    
    def sync_transactions(self, bank_connection, days=30):
        """Synchronize transactions from PUMB to database"""
        sync_log = SyncLog.objects.create(
            user=bank_connection.user,
            source='pumb',
            status='pending'
        )
        
        try:
            # Get all accounts
            accounts = self.get_accounts()
            
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            total_transactions = 0
            
            for account in accounts.get('accounts', []):
                account_id = account.get('id')
                
                # Get transactions for this account
                transactions_data = self.get_transactions(account_id, from_date, to_date)
                
                for trans in transactions_data.get('transactions', []):
                    transaction_id = f"pumb_{trans.get('id')}"
                    
                    # Check if transaction already exists
                    if Transaction.objects.filter(source='pumb', source_id=transaction_id).exists():
                        continue
                    
                    # Determine transaction type
                    amount = float(trans.get('amount', 0))
                    trans_type = 'income' if amount > 0 else 'expense'
                    
                    # Get or create category
                    category_name = self._classify_transaction(trans)
                    category, _ = TransactionCategory.objects.get_or_create(
                        user=bank_connection.user,
                        name=category_name,
                        defaults={'type': trans_type}
                    )
                    
                    # Create transaction
                    Transaction.objects.create(
                        user=bank_connection.user,
                        source='pumb',
                        source_id=transaction_id,
                        amount=abs(amount),
                        currency=trans.get('currency', 'UAH'),
                        type=trans_type,
                        description=trans.get('description', ''),
                        category=category,
                        counterparty=trans.get('merchant', ''),
                        transaction_date=datetime.fromtimestamp(trans.get('timestamp', 0))
                    )
                    
                    total_transactions += 1
            
            # Update bank connection
            bank_connection.last_sync = datetime.now()
            bank_connection.status = 'active'
            bank_connection.save()
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.transactions_count = total_transactions
            sync_log.completed_at = datetime.now()
            sync_log.save()
            
            return {
                'success': True,
                'transactions_synced': total_transactions
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.now()
            sync_log.save()
            
            raise Exception(f"Sync failed: {str(e)}")
    
    def _classify_transaction(self, transaction):
        """Classify transaction by description and merchant"""
        description = transaction.get('description', '').lower()
        merchant = transaction.get('merchant', '').lower()
        
        # Mapping based on keywords
        if any(word in description or word in merchant for word in ['atm', 'банкомат', 'зняття']):
            return 'Зняття готівки'
        elif any(word in description or word in merchant for word in ['transfer', 'переказ']):
            return 'Перекази'
        elif any(word in description or word in merchant for word in ['salary', 'зарплата', 'заробітна']):
            return 'Зарплата'
        elif any(word in description or word in merchant for word in ['silpo', 'атб', 'auchan', 'продукти']):
            return 'Продукти'
        elif any(word in description or word in merchant for word in ['restaurant', 'cafe', 'ресторан', 'кафе']):
            return 'Ресторани і кафе'
        elif any(word in description or word in merchant for word in ['transport', 'taxi', 'bolt', 'uber', 'транспорт']):
            return 'Транспорт'
        elif any(word in description or word in merchant for word in ['pharmacy', 'аптека']):
            return 'Аптека'
        elif any(word in description or word in merchant for word in ['clothing', 'одяг', 'fashion']):
            return 'Одяг та взуття'
        
        return 'Інше'
    
    @staticmethod
    def validate_token(access_token):
        """Validate PUMB access token"""
        service = PUMBService(access_token)
        try:
            service.get_accounts()
            return True
        except:
            return False
