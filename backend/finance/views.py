from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    BankConnection, CryptoExchange, Transaction,
    TransactionCategory, FinancialForecast, SyncLog
)
from .serializers import (
    BankConnectionSerializer, AddBankConnectionSerializer,
    CryptoExchangeSerializer, AddCryptoExchangeSerializer,
    TransactionSerializer, TransactionCategorySerializer,
    FinancialForecastSerializer, SyncLogSerializer,
    SyncRequestSerializer
)
from .services.monobank import MonobankService
from .services.pumb import PUMBService
from .services.binance import BinanceService
from .services.bybit import BybitService
from .services.okx import OKXService


class BankConnectionListView(generics.ListAPIView):
    """Список підключень до банків"""
    serializer_class = BankConnectionSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return BankConnection.objects.filter(user=self.request.user)


class AddBankConnectionView(views.APIView):
    """Додати підключення до банку"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        request_body=AddBankConnectionSerializer,
        responses={
            201: BankConnectionSerializer,
            400: "Помилка валідації або неправильний токен"
        }
    )
    def post(self, request):
        serializer = AddBankConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        name = serializer.validated_data.get('name', '')
        bank_name = serializer.validated_data['bank_name']
        access_token = serializer.validated_data['access_token']
        
        # Перевіряємо токен
        if bank_name == 'monobank':
            if not MonobankService.validate_token(access_token):
                return Response(
                    {'error': 'Невалідний токен Monobank'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif bank_name == 'pumb':
            if not PUMBService.validate_token(access_token):
                return Response(
                    {'error': 'Невалідний токен ПУМБ'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Створюємо або оновлюємо підключення
        bank_connection, created = BankConnection.objects.update_or_create(
            user=request.user,
            bank_name=bank_name,
            defaults={
                'name': name or bank_name.capitalize(),
                'access_token': access_token,
                'status': 'active'
            }
        )
        
        return Response(
            BankConnectionSerializer(bank_connection).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class DeleteBankConnectionView(views.APIView):
    """Видалити підключення до банку"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        responses={
            204: "Підключення видалено",
            404: "Підключення не знайдено"
        }
    )
    def delete(self, request, pk):
        try:
            connection = BankConnection.objects.get(pk=pk, user=request.user)
            connection.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BankConnection.DoesNotExist:
            return Response(
                {'error': 'Підключення не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )


class CryptoExchangeListView(generics.ListAPIView):
    """Список підключень до бірж"""
    serializer_class = CryptoExchangeSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return CryptoExchange.objects.filter(user=self.request.user)


class AddCryptoExchangeView(views.APIView):
    """Додати підключення до біржі"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        request_body=AddCryptoExchangeSerializer,
        responses={
            201: CryptoExchangeSerializer,
            400: "Помилка валідації"
        }
    )
    def post(self, request):
        serializer = AddCryptoExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        exchange_name = serializer.validated_data['exchange_name']
        api_key = serializer.validated_data['api_key']
        api_secret = serializer.validated_data['api_secret']
        api_passphrase = serializer.validated_data.get('api_passphrase', '')
        
        # Перевіряємо API ключі
        if exchange_name == 'binance':
            if not BinanceService.validate_credentials(api_key, api_secret):
                return Response(
                    {'error': 'Невалідні API ключі Binance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif exchange_name == 'bybit':
            if not BybitService.validate_credentials(api_key, api_secret):
                return Response(
                    {'error': 'Невалідні API ключі Bybit'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif exchange_name == 'okx':
            if not OKXService.validate_credentials(api_key, api_secret, api_passphrase):
                return Response(
                    {'error': 'Невалідні API ключі OKX'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        exchange, created = CryptoExchange.objects.update_or_create(
            user=request.user,
            exchange_name=exchange_name,
            defaults={
                'api_key': api_key,
                'api_secret': api_secret,
                'api_passphrase': api_passphrase,
                'status': 'active'
            }
        )
        
        return Response(
            CryptoExchangeSerializer(exchange).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class DeleteCryptoExchangeView(views.APIView):
    """Видалити підключення до біржі"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        responses={
            204: "Підключення видалено",
            404: "Підключення не знайдено"
        }
    )
    def delete(self, request, pk):
        try:
            exchange = CryptoExchange.objects.get(pk=pk, user=request.user)
            exchange.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CryptoExchange.DoesNotExist:
            return Response(
                {'error': 'Підключення не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )


class TransactionListView(views.APIView):
    """Список транзакцій з API банків та бірж"""
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        source = request.query_params.get('source', 'all')
        days = int(request.query_params.get('days', 30))
        
        all_transactions = []
        
        try:
            # Якщо source='all' або 'monobank', завантажуємо з Monobank
            if source in ['all', 'monobank']:
                try:
                    bank = BankConnection.objects.get(
                        user=request.user,
                        bank_name='monobank',
                        status='active'
                    )
                    monobank_transactions = MonobankService.get_transactions(
                        bank.access_token,
                        days=days
                    )
                    all_transactions.extend(monobank_transactions)
                except BankConnection.DoesNotExist:
                    pass
            
            # Якщо source='all' або 'pumb', завантажуємо з ПУМБ
            if source in ['all', 'pumb']:
                try:
                    bank = BankConnection.objects.get(
                        user=request.user,
                        bank_name='pumb',
                        status='active'
                    )
                    # TODO: Додати сервіс для ПУМБ
                    # pumb_transactions = PUMBService.get_transactions(bank.access_token, days=days)
                    # all_transactions.extend(pumb_transactions)
                except BankConnection.DoesNotExist:
                    pass
            
            # Сортуємо по даті (найновіші першими)
            all_transactions.sort(key=lambda x: x['transaction_date'], reverse=True)
            
            return Response(all_transactions)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SyncView(views.APIView):
    """Синхронізація транзакцій"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        request_body=SyncRequestSerializer,
        responses={
            200: openapi.Response(
                description="Синхронізація успішна",
                examples={
                    "application/json": {
                        "success": True,
                        "transactions_added": 10,
                        "transactions_updated": 5
                    }
                }
            ),
            400: "Помилка синхронізації",
            404: "Підключення не знайдено"
        }
    )
    def post(self, request):
        serializer = SyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        source = serializer.validated_data['source']
        days = serializer.validated_data['days']
        
        try:
            if source == 'monobank':
                connection = BankConnection.objects.get(
                    user=request.user,
                    bank_name='monobank'
                )
                service = MonobankService(request.user)
                result = service.sync_transactions(connection, days=days)
                return Response(result)
            
            elif source == 'pumb':
                connection = BankConnection.objects.get(
                    user=request.user,
                    bank_name='pumb'
                )
                service = PUMBService(connection.access_token)
                result = service.sync_transactions(connection, days=days)
                return Response(result)
            
            elif source == 'binance':
                exchange = CryptoExchange.objects.get(
                    user=request.user,
                    exchange_name='binance'
                )
                service = BinanceService(exchange.api_key, exchange.api_secret)
                result = service.sync_transactions(exchange, days=days)
                return Response(result)
            
            elif source == 'bybit':
                exchange = CryptoExchange.objects.get(
                    user=request.user,
                    exchange_name='bybit'
                )
                service = BybitService(exchange.api_key, exchange.api_secret)
                result = service.sync_transactions(exchange, days=days)
                return Response(result)
            
            elif source == 'okx':
                exchange = CryptoExchange.objects.get(
                    user=request.user,
                    exchange_name='okx'
                )
                service = OKXService(exchange.api_key, exchange.api_secret, exchange.api_passphrase)
                result = service.sync_transactions(exchange, days=days)
                return Response(result)
            
            else:
                return Response(
                    {'error': 'Невідоме джерело'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (BankConnection.DoesNotExist, CryptoExchange.DoesNotExist):
            return Response(
                {'error': 'Підключення не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SyncLogListView(generics.ListAPIView):
    """Список логів синхронізації"""
    serializer_class = SyncLogSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return SyncLog.objects.filter(user=self.request.user)[:20]


class TransactionCategoryListView(generics.ListCreateAPIView):
    """Список категорій транзакцій"""
    serializer_class = TransactionCategorySerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return TransactionCategory.objects.all()


class PUMBAuthInitView(views.APIView):
    """Ініціювати OAuth2 авторизацію ПУМБ"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="URL для авторизації",
                examples={
                    "application/json": {
                        "authorization_url": "https://auth.pumb.ua/oauth/authorize?..."
                    }
                }
            )
        }
    )
    def get(self, request):
        from django.conf import settings
        import secrets
        
        # Генеруємо state для захисту від CSRF
        state = secrets.token_urlsafe(32)
        request.session['pumb_oauth_state'] = state
        
        client_id = settings.PUMB_CLIENT_ID
        redirect_uri = settings.PUMB_REDIRECT_URI
        
        if not client_id:
            return Response(
                {'error': 'PUMB OAuth2 не налаштовано'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        auth_url = PUMBService.get_authorization_url(client_id, redirect_uri, state)
        
        return Response({
            'authorization_url': auth_url
        })


class PUMBAuthCallbackView(views.APIView):
    """Callback для OAuth2 авторизації ПУМБ"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('state', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: BankConnectionSerializer,
            400: "Помилка авторизації"
        }
    )
    def get(self, request):
        from django.conf import settings
        
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        
        # Перевіряємо state
        stored_state = request.session.get('pumb_oauth_state')
        if not stored_state or stored_state != state:
            return Response(
                {'error': 'Невалідний state'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Обмінюємо код на токен
            token_data = PUMBService.exchange_code_for_token(
                code,
                settings.PUMB_CLIENT_ID,
                settings.PUMB_CLIENT_SECRET,
                settings.PUMB_REDIRECT_URI
            )
            
            # Зберігаємо підключення
            bank_connection, created = BankConnection.objects.update_or_create(
                user=request.user,
                bank_name='pumb',
                defaults={
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token', ''),
                    'status': 'active'
                }
            )
            
            # Очищаємо state з сесії
            del request.session['pumb_oauth_state']
            
            return Response(
                BankConnectionSerializer(bank_connection).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExchangeBalanceView(views.APIView):
    """Отримати баланс біржі"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        responses={
            200: "Баланс отримано",
            404: "Підключення не знайдено"
        }
    )
    def get(self, request):
        exchange_name = request.query_params.get('exchange', 'bybit')
        
        try:
            exchange = CryptoExchange.objects.get(
                user=request.user,
                exchange_name=exchange_name,
                status='active'
            )
            
            if exchange_name == 'bybit':
                service = BybitService(exchange.api_key, exchange.api_secret)
                balance = service.get_wallet_balance()
                return Response(balance)
            
            # Тут можна додати інші біржі
            
            return Response({'error': 'Біржа не підтримується'}, status=status.HTTP_400_BAD_REQUEST)
            
        except CryptoExchange.DoesNotExist:
            return Response(
                {'error': 'Підключення не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExchangeOrdersView(views.APIView):
    """Отримати відкриті ордери"""
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        responses={
            200: "Ордери отримано",
            404: "Підключення не знайдено"
        }
    )
    def get(self, request):
        exchange_name = request.query_params.get('exchange', 'bybit')
        category = request.query_params.get('category', 'spot')
        symbol = request.query_params.get('symbol')
        settle_coin = request.query_params.get('settleCoin')
        
        try:
            exchange = CryptoExchange.objects.get(
                user=request.user,
                exchange_name=exchange_name,
                status='active'
            )
            
            if exchange_name == 'bybit':
                service = BybitService(exchange.api_key, exchange.api_secret)
                
                # Для linear категорії потрібен settleCoin або symbol
                if category == 'linear' and not symbol and not settle_coin:
                    settle_coin = 'USDT'
                
                orders = service.get_open_orders(
                    category=category,
                    symbol=symbol,
                    settleCoin=settle_coin
                )
                return Response(orders)
            
            return Response({'error': 'Біржа не підтримується'}, status=status.HTTP_400_BAD_REQUEST)
            
        except CryptoExchange.DoesNotExist:
            return Response(
                {'error': 'Підключення не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankAnalyticsView(views.APIView):
    """Аналітика банківського рахунку"""
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        try:
            # Отримуємо транзакції користувача
            bank = BankConnection.objects.filter(
                user=request.user,
                bank_name='monobank',
                status='active'
            ).first()
            
            if not bank:
                return Response({'error': 'Банк не підключено'}, status=status.HTTP_404_NOT_FOUND)
            
            # Завантажуємо транзакції
            transactions = MonobankService.get_transactions(bank.access_token, days=30)
            
            # Рахуємо баланс (це приклад, в реальності треба отримувати з API)
            balance = sum(
                t['amount'] if t['type'] == 'income' else -t['amount']
                for t in transactions
            )
            
            return Response({
                'balance': balance,
                'transactions': transactions
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
