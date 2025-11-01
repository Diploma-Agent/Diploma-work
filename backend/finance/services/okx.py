"""
OKX Exchange API Integration Service
https://www.okx.com/docs-v5/en/
"""
import requests
import hmac
import hashlib
import base64
import time
from datetime import datetime, timedelta
from finance.models import Transaction, TransactionCategory, SyncLog


class OKXService:
    """Service for OKX API integration"""
    
    BASE_URL = "https://www.okx.com"
    
    def __init__(self, api_key, api_secret, api_passphrase):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
    
    def _generate_signature(self, timestamp, method, request_path, body=''):
        """Generate signature for OKX API"""
        message = f"{timestamp}{method}{request_path}{body}"
        mac = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode('utf-8')
    
    def _make_request(self, method, endpoint, params=None):
        """Make authenticated request to OKX API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        
        body = ''
        if params and method == 'POST':
            import json
            body = json.dumps(params)
        
        # Add query params for GET requests
        query_string = ''
        if params and method == 'GET':
            query_string = '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
            endpoint = endpoint + query_string
        
        signature = self._generate_signature(timestamp, method, endpoint, body)
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.api_passphrase,
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=body)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != '0':
                raise Exception(f"OKX API error: {data.get('msg')}")
            
            return data.get('data', [])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"OKX API request failed: {str(e)}")
    
    def get_account_balance(self):
        """Get account balance"""
        return self._make_request('GET', '/api/v5/account/balance')
    
    def get_bills(self, inst_type='SPOT', limit=100):
        """Get account bills (transaction history)"""
        params = {
            'instType': inst_type,
            'limit': limit
        }
        return self._make_request('GET', '/api/v5/account/bills', params)
    
    def get_fills_history(self, inst_type='SPOT', limit=100):
        """Get fills (executed orders) history"""
        params = {
            'instType': inst_type,
            'limit': limit
        }
        return self._make_request('GET', '/api/v5/trade/fills-history', params)
    
    def sync_transactions(self, crypto_exchange, days=30):
        """Synchronize trades from OKX to database"""
        sync_log = SyncLog.objects.create(
            user=crypto_exchange.user,
            source='okx',
            status='pending'
        )
        
        try:
            total_transactions = 0
            
            # Get fills (executed trades)
            fills = self.get_fills_history(inst_type='SPOT', limit=100)
            
            for trade in fills:
                transaction_id = f"okx_{trade.get('tradeId')}"
                
                # Check if transaction already exists
                if Transaction.objects.filter(source='okx', source_id=transaction_id).exists():
                    continue
                
                # Determine if buy or sell
                side = trade.get('side', 'buy')
                is_buy = side == 'buy'
                
                sz = float(trade.get('sz', 0))  # Size
                px = float(trade.get('px', 0))  # Price
                fee = float(trade.get('fee', 0))
                fill_sz = float(trade.get('fillSz', 0))
                
                # Calculate value
                value = sz * px
                
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
                    source='okx',
                    source_id=transaction_id,
                    amount=value,
                    currency='USDT',
                    type=trans_type,
                    description=f"{side.upper()} {sz} {trade.get('instId', '')} @ {px}",
                    category=category,
                    counterparty='OKX',
                    transaction_date=datetime.fromtimestamp(int(trade.get('ts', 0)) / 1000)
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
    def validate_credentials(api_key, api_secret, api_passphrase):
        """Validate OKX API credentials"""
        service = OKXService(api_key, api_secret, api_passphrase)
        try:
            service.get_account_balance()
            return True
        except:
            return False
