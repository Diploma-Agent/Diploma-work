"""
Bybit Exchange API Integration Service
https://bybit-exchange.github.io/docs/v5/intro
"""
import requests
import hmac
import hashlib
import time
import json
from datetime import datetime, timedelta
from finance.models import Transaction, TransactionCategory, SyncLog


class BybitService:
    """Service for Bybit API integration"""
    
    BASE_URL = "https://api.bybit.com"
    
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
    
    def _generate_signature(self, timestamp, params_str):
        """Generate HMAC SHA256 signature for Bybit"""
        param_str = f"{timestamp}{self.api_key}{params_str}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method, endpoint, params=None):
        """Make authenticated request to Bybit API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
            
        # Додаємо recvWindow для компенсації розсинхронізації часу
        params['recvWindow'] = 20000
        
        # Використовуємо поточний час мінус 2 секунди, щоб уникнути помилки "timestamp in the future"
        # якщо годинник клієнта поспішає
        timestamp = str(int((time.time() - 2) * 1000))
        
        if method == 'GET':
            # Sort parameters for GET request
            sorted_params = sorted(params.items())
            params_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
            
            # Generate signature
            signature = self._generate_signature(timestamp, params_str)
            
            headers = {
                'X-BAPI-API-KEY': self.api_key,
                'X-BAPI-TIMESTAMP': timestamp,
                'X-BAPI-SIGN': signature
            }
            
            # Pass sorted_params to requests to ensure sending order matches signing order
            response = requests.get(url, headers=headers, params=sorted_params)
            
        elif method == 'POST':
            # For POST, params_str is the JSON string
            # Use separators to remove spaces
            params_json = json.dumps(params)
            
            signature = self._generate_signature(timestamp, params_json)
            
            headers = {
                'X-BAPI-API-KEY': self.api_key,
                'X-BAPI-TIMESTAMP': timestamp,
                'X-BAPI-SIGN': signature,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=params_json)
        
        try:
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') != 0:
                raise Exception(f"Bybit API error: {data.get('retMsg')}")
            
            return data.get('result', {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Bybit API request failed: {str(e)}")
    
    def get_wallet_balance(self, account_type='UNIFIED'):
        """Get wallet balance"""
        params = {'accountType': account_type}
        return self._make_request('GET', '/v5/account/wallet-balance', params)
    
    def get_transaction_log(self, category='spot', limit=50):
        """Get transaction log"""
        params = {
            'category': category,
            'limit': limit
        }
        return self._make_request('GET', '/v5/account/transaction-log', params)
    
    def get_execution_list(self, category='spot', limit=50):
        """Get execution (trade) list"""
        params = {
            'category': category,
            'limit': limit
        }
        return self._make_request('GET', '/v5/execution/list', params)
    
    def get_open_orders(self, category='spot', symbol=None, settleCoin=None, limit=50):
        """Get open orders"""
        params = {
            'category': category,
            'limit': limit
        }
        if symbol:
            params['symbol'] = symbol
        if settleCoin:
            params['settleCoin'] = settleCoin
            
        return self._make_request('GET', '/v5/order/realtime', params)
    
    def sync_transactions(self, crypto_exchange, days=30):
        """Synchronize trades from Bybit to database"""
        sync_log = SyncLog.objects.create(
            user=crypto_exchange.user,
            source='bybit',
            status='pending'
        )
        
        try:
            total_transactions = 0
            
            # Get executions (trades) for spot trading
            executions = self.get_execution_list(category='spot', limit=100)
            
            for trade in executions.get('list', []):
                transaction_id = f"bybit_{trade.get('execId')}"
                
                # Check if transaction already exists
                if Transaction.objects.filter(source='bybit', source_id=transaction_id).exists():
                    continue
                
                # Determine if buy or sell
                side = trade.get('side', 'Buy')
                is_buy = side == 'Buy'
                
                qty = float(trade.get('execQty', 0))
                price = float(trade.get('execPrice', 0))
                value = float(trade.get('execValue', 0))
                fee = float(trade.get('execFee', 0))
                
                # Get or create category
                category_name = 'Купівля криптовалюти' if is_buy else 'Продаж криптовалюти'
                trans_type = 'expense' if is_buy else 'income'
                
                category, _ = TransactionCategory.objects.get_or_create(
                    user=crypto_exchange.user,
                    name=category_name,
                    defaults={'type': trans_type}
                )
                
                # Create transaction
                Transaction.objects.create(
                    user=crypto_exchange.user,
                    source='bybit',
                    source_id=transaction_id,
                    amount=value / 1e8,  # Bybit uses satoshi units
                    currency='USDT',
                    type=trans_type,
                    description=f"{side} {qty} {trade.get('symbol', '')} @ {price}",
                    category=category,
                    counterparty='Bybit',
                    transaction_date=datetime.fromtimestamp(int(trade.get('execTime', 0)) / 1000)
                )
                
                total_transactions += 1
            
            # Update exchange connection
            crypto_exchange.last_sync = datetime.now()
            crypto_exchange.status = 'active'
            crypto_exchange.save()
            
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
    
    @staticmethod
    def validate_credentials(api_key, api_secret):
        """Validate Bybit API credentials"""
        service = BybitService(api_key, api_secret)
        try:
            # Спроба 1: Перевірка для Unified Account
            service.get_wallet_balance(account_type='UNIFIED')
            return True
        except Exception:
            try:
                # Спроба 2: Перевірка для Standard Account (SPOT)
                service.get_wallet_balance(account_type='SPOT')
                return True
            except Exception:
                return False
