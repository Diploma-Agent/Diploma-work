"""
Binance Exchange API Integration Service
https://binance-docs.github.io/apidocs/spot/en/
"""
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone
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
        """Make authenticated request to Binance API.

        Підпис будується на точному query string що буде відправлений —
        це гарантує відповідність підпису і уникає 401 через порядок params.
        """
        # Якщо endpoint — повний URL (futures тощо), використовуємо його напряму
        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = f"{self.BASE_URL}{endpoint}"

        if params is None:
            params = {}

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            # Будуємо query string в тому ж порядку що й підписуємо
            query_string = urlencode(params)
            signature = self._generate_signature(query_string)
            # Підпис додаємо в кінець — саме так Binance очікує
            full_url = f"{url}?{query_string}&signature={signature}"
        else:
            full_url = url

        try:
            if method == 'GET':
                response = requests.get(full_url, headers=self.headers, timeout=15)
            elif method == 'POST':
                response = requests.post(full_url, headers=self.headers, timeout=15)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 0
            if status_code == 451:
                raise Exception("Binance недоступний з цього регіону сервера (451 geo-restriction)")
            if status_code == 418:
                raise Exception("Binance заблокував запит (418) — futures акаунт відсутній або IP заблоковано")
            if status_code == 401:
                raise Exception("Binance 401 Unauthorized — перевірте що в API ключі увімкнено 'Enable Reading'")
            raise Exception(f"Binance API request failed: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Binance API request failed: {str(e)}")

    def get_account_info(self):
        """Get account information (Spot)"""
        return self._make_request('GET', '/api/v3/account')
    
    def get_user_assets(self, need_btc_valuation=True):
        """
        Get all user assets (Spot, Funding, etc.)
        Requires "Permit Universal Transfer" and "Enable Spot & Margin Trading" API Key permissions.
        """
        try:
            params = {}
            if need_btc_valuation:
                params['needBtcValuation'] = 'true'
            # SAPI endpoint for user assets
            return self._make_request('POST', '/sapi/v1/asset/get-user-asset', params=params, signed=True)
        except Exception as e:
            print(f"Failed to fetch user assets (SAPI): {str(e)}")
            return []

    def get_futures_balances(self):
        """Get USDT-M Futures account balances"""
        try:
            result = self._make_request('GET', 'https://fapi.binance.com/fapi/v2/account', {})
            return result.get('assets', [])
        except Exception as e:
            print(f"Failed to fetch futures assets: {str(e)}")
            return []

    def get_balances(self):
        """Get account balances (Combined: Spot + Funding + Futures)"""
        balances_map = {} # asset_name -> {'free': 0, 'locked': 0}

        def add_to_map(asset_name, free, locked):
            if not asset_name: return
            free_val = float(free or 0)
            locked_val = float(locked or 0)
            if free_val <= 0 and locked_val <= 0: return
            
            if asset_name in balances_map:
                balances_map[asset_name]['free'] += free_val
                balances_map[asset_name]['locked'] += locked_val
            else:
                balances_map[asset_name] = {'free': free_val, 'locked': locked_val}

        # 1. Spot (API v3)
        try:
            spot_info = self.get_account_info()
            for b in spot_info.get('balances', []):
                add_to_map(b.get('asset'), b.get('free'), b.get('locked'))
        except Exception: pass

        # 2. Funding (SAPI) — опціонально, потребує додаткових прав
        try:
            funding_assets = self.get_user_assets()
            for asset in funding_assets:
                f = float(asset.get('free', 0))
                l = float(asset.get('locked', 0)) + float(asset.get('freeze', 0)) + float(asset.get('withdrawing', 0))
                add_to_map(asset.get('asset'), f, l)
        except Exception:
            pass  # Не критично — основний баланс є в Spot

        # 3. Futures (FAPI)
        try:
            futures_assets = self.get_futures_balances()
            for asset in futures_assets:
                bal = float(asset.get('walletBalance', 0))
                if bal > 0:
                    add_to_map(asset.get('asset'), bal, 0)
        except Exception: pass

        # Final list mapping
        final_balances = []
        for asset, data in balances_map.items():
            final_balances.append({
                'asset': asset,
                'free': data['free'],
                'locked': data['locked'],
                'total': data['free'] + data['locked']
            })
        
        return final_balances
    
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
    
    def get_open_orders(self, category='spot', symbol=None, limit=50):
        """Get open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
            
        endpoint = '/api/v3/openOrders'
        if category == 'linear':
            endpoint = 'https://fapi.binance.com/fapi/v1/openOrders'
            # Note: _make_request logic might need special handling if it prefixes self.BASE_URL
            # For simplicity, if we rely on standard SPOT open orders:
            pass # TODO: handle futures appropriately if needed
            
        return self._make_request('GET', '/api/v3/openOrders', params)
    
    
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
                            connection_id=crypto_exchange.id,
                            amount=quote_qty,
                            currency='USDT',
                            type=trans_type,
                            description=f"{'Buy' if is_buyer else 'Sell'} {qty} {symbol.replace('USDT', '')} @ {price}",
                            category=category,
                            counterparty='Binance',
                            transaction_date=datetime.fromtimestamp(trade.get('time', 0) / 1000, tz=dt_timezone.utc)
                        )
                        
                        total_transactions += 1
                        
                except Exception as e:
                    # Continue with other symbols if one fails
                    continue
            
            # Update exchange connection
            crypto_exchange.last_sync = timezone.now()
            crypto_exchange.status = 'active'
            crypto_exchange.save()
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.transactions_count = total_transactions
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            return {
                'success': True,
                'transactions_synced': total_transactions
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
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
