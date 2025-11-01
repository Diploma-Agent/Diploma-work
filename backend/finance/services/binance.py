"""
Binance Exchange API Integration Service
https://binance-docs.github.io/apidocs/spot/en/
"""
import requests
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from finance.models import Transaction, TransactionCategory, SyncLog


class BinanceService:
    """Service for Binance API integration"""
    
    BASE_URL = "https://api.binance.com"
    
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {
            'X-MBX-APIKEY': api_key
        }
    
    def _generate_signature(self, query_string):
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method, endpoint, params=None, signed=True):
        """Make authenticated request to Binance API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, params=params)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Binance API request failed: {str(e)}")
    
    def get_account_info(self):
        """Get account information"""
        return self._make_request('GET', '/api/v3/account')
    
    def get_balances(self):
        """Get account balances"""
        account_info = self.get_account_info()
        balances = []
        
        for balance in account_info.get('balances', []):
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            
            if free > 0 or locked > 0:
                balances.append({
                    'asset': balance.get('asset'),
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                })
        
        return balances
    
    def get_trades(self, symbol, limit=500):
        """Get recent trades for a symbol"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/api/v3/myTrades', params)
    
    def get_all_orders(self, symbol, start_time=None, end_time=None):
        """Get all orders for a symbol"""
        params = {'symbol': symbol}
        
        if start_time:
            params['startTime'] = int(start_time.timestamp() * 1000)
        if end_time:
            params['endTime'] = int(end_time.timestamp() * 1000)
        
        return self._make_request('GET', '/api/v3/allOrders', params)
    
    def sync_transactions(self, crypto_exchange, days=30):
        """Synchronize trades from Binance to database"""
        sync_log = SyncLog.objects.create(
            user=crypto_exchange.user,
            source='binance',
            status='pending'
        )
        
        try:
            # Get account balances to determine which symbols to check
            balances = self.get_balances()
            
            # Common trading pairs
            trading_pairs = []
            for balance in balances:
                asset = balance['asset']
                if asset != 'USDT':
                    trading_pairs.append(f"{asset}USDT")
            
            # Also add common pairs
            common_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
            trading_pairs.extend(common_pairs)
            trading_pairs = list(set(trading_pairs))  # Remove duplicates
            
            total_transactions = 0
            
            for symbol in trading_pairs:
                try:
                    trades = self.get_trades(symbol, limit=100)
                    
                    for trade in trades:
                        transaction_id = f"binance_{trade.get('id')}"
                        
                        # Check if transaction already exists
                        if Transaction.objects.filter(source='binance', source_id=transaction_id).exists():
                            continue
                        
                        # Determine if buy or sell
                        is_buyer = trade.get('isBuyer', True)
                        qty = float(trade.get('qty', 0))
                        price = float(trade.get('price', 0))
                        commission = float(trade.get('commission', 0))
                        quote_qty = float(trade.get('quoteQty', 0))
                        
                        # Get or create category
                        category_name = 'Купівля криптовалюти' if is_buyer else 'Продаж криптовалюти'
                        trans_type = 'expense' if is_buyer else 'income'
                        
                        category, _ = TransactionCategory.objects.get_or_create(
                            user=crypto_exchange.user,
                            name=category_name,
                            defaults={'type': trans_type}
                        )
                        
                        # Create transaction
                        Transaction.objects.create(
                            user=crypto_exchange.user,
                            source='binance',
                            source_id=transaction_id,
                            amount=quote_qty,
                            currency='USDT',
                            type=trans_type,
                            description=f"{'Buy' if is_buyer else 'Sell'} {qty} {symbol.replace('USDT', '')} @ {price}",
                            category=category,
                            counterparty='Binance',
                            transaction_date=datetime.fromtimestamp(trade.get('time', 0) / 1000)
                        )
                        
                        total_transactions += 1
                        
                except Exception as e:
                    # Continue with other symbols if one fails
                    continue
            
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
        """Validate Binance API credentials"""
        service = BinanceService(api_key, api_secret)
        try:
            service.get_account_info()
            return True
        except:
            return False
