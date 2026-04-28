from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import traceback
import secrets
import pytz
from datetime import datetime
from django.conf import settings

from .models import (
    BankConnection, CryptoExchange, Transaction,
    TransactionCategory, FinancialForecast, SyncLog, ChatMessage
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
from .services.ai_agents import (
    FinancialAnalystAgent,
    InvestmentAdvisorAgent,
    ForecastAgent,
    AnomalyDetectorAgent,
    ChatAgent
)


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
            all_transactions.sort(
                key=lambda x: x['transaction_date'], reverse=True)

            return Response(all_transactions)

        except Exception as e:
            traceback.print_exc()
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
                service = OKXService(
                    exchange.api_key, exchange.api_secret, exchange.api_passphrase)
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
        # Генеруємо state для захисту від CSRF
        state = secrets.token_urlsafe(32)
        request.session['pumb_oauth_state'] = state

        client_id = getattr(settings, 'PUMB_CLIENT_ID', None)
        redirect_uri = getattr(settings, 'PUMB_REDIRECT_URI', None)

        if not client_id:
            return Response(
                {'error': 'PUMB OAuth2 не налаштовано'},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_url = PUMBService.get_authorization_url(
            client_id, redirect_uri, state)

        return Response({
            'authorization_url': auth_url
        })


class PUMBAuthCallbackView(views.APIView):
    """Callback для OAuth2 авторизації ПУМБ"""
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_QUERY,
                              type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('state', openapi.IN_QUERY,
                              type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: BankConnectionSerializer,
            400: "Помилка авторизації"
        }
    )
    def get(self, request):
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
            elif exchange_name == 'okx':
                service = OKXService(exchange.api_key, exchange.api_secret, exchange.api_passphrase)
                raw_balance = service.get_account_balance()
                
                # Форматуємо відповідь зі структури OKX до структури, що очікується на клієнті (як у Bybit)
                if raw_balance and len(raw_balance) > 0:
                    data = raw_balance[0]
                    coins = []
                    for d in data.get('details', []):
                        coins.append({
                            'coin': d.get('ccy', ''),
                            'walletBalance': d.get('eq', '0'),
                            'usdValue': d.get('eqUsd', '0')
                        })
                    formatted = {
                        'list': [{
                            'totalEquity': data.get('totalEq', '0'),
                            'coin': coins
                        }]
                    }
                else:
                    formatted = {'list': [{'totalEquity': '0', 'coin': []}]}
                
                return Response(formatted)
            elif exchange_name == 'binance':
                service = BinanceService(exchange.api_key, exchange.api_secret)
                raw_balance = service.get_balances()
                
                # Аналогічно формуємо дані для Binance
                coins = []
                for b in raw_balance:
                    free = float(b.get('free', 0))
                    locked = float(b.get('locked', 0))
                    bal = free + locked
                    if bal > 0:
                        coins.append({
                            'coin': b.get('asset', ''),
                            'walletBalance': str(bal),
                            'usdValue': '0' # Binance get_balances не повертає usdValue
                        })
                formatted = {
                    'list': [{
                        'totalEquity': '0',
                        'coin': coins
                    }]
                }
                return Response(formatted)

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
            elif exchange_name == 'okx':
                service = OKXService(exchange.api_key, exchange.api_secret, exchange.api_passphrase)
                orders = service.get_open_orders(
                    category=category,
                    symbol=symbol
                )
                # Повертаємо об'єкт зі списком ордерів, щоб відповідати формат обробки на фронтенді (result.list або list)
                return Response({'list': orders})
            elif exchange_name == 'binance':
                service = BinanceService(exchange.api_key, exchange.api_secret)
                raw_orders = service.get_open_orders(
                    category=category,
                    symbol=symbol
                )
                formatted_orders = []
                for ord in raw_orders:
                    formatted_orders.append({
                        'orderId': ord.get('orderId'),
                        'symbol': ord.get('symbol'),
                        'side': ord.get('side'),
                        'price': ord.get('price'),
                        'qty': ord.get('origQty'),
                        'orderStatus': ord.get('status')
                    })
                return Response({'list': formatted_orders})

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
            bank = BankConnection.objects.filter(
                user=request.user,
                bank_name='monobank',
                status='active'
            ).first()

            if not bank:
                return Response({'error': 'Банк не підключено'}, status=status.HTTP_404_NOT_FOUND)

            # Баланс тільки основних рахунків (без накопичувальних/кредитних)
            balance, _ = _get_real_balance(bank.access_token)

            # Транзакції тільки з основних UAH-рахунків, без внутрішніх переказів
            transactions = _get_uah_transactions(bank.access_token, days=30)

            return Response({
                'balance': balance,
                'transactions': transactions
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


def _get_real_balance(access_token: str) -> tuple:
    """Реальний баланс + список UAH рахунків (не кредитних)"""
    try:
        client_info = MonobankService.get_client_info(access_token)
        accounts = client_info.get('accounts', [])

        # Логуємо всі рахунки для дебагу
        for acc in accounts:
            print(f"Account: id={acc.get('id')}, type={acc.get('type')}, "
                  f"currency={acc.get('currencyCode')}, balance={acc.get('balance', 0)/100}")

        # Основний чорний рахунок (тип 'black') — дебетова карта
        main_accounts = [
            acc for acc in accounts
            if acc.get('currencyCode') == 980
            and acc.get('type') in ['black', 'white', 'yellow', 'iron', 'platinum', 'other']
        ]

        balance = sum(acc['balance'] / 100 for acc in main_accounts)
        main_account_ids = [acc['id'] for acc in main_accounts]

        return balance, main_account_ids
    except Exception as e:
        print(f"_get_real_balance error: {e}")
        return 0.0, []


def _get_uah_transactions(access_token: str, days: int = 30) -> list:
    """Транзакції тільки з основних UAH рахунків (без кредитних)"""
    try:
        balance, main_account_ids = _get_real_balance(access_token)
        all_transactions = MonobankService.get_transactions(
            access_token, days=days)

        # Якщо є account_id — фільтруємо по основних рахунках
        if main_account_ids:
            filtered = [
                t for t in all_transactions
                if t.get('account_id') in main_account_ids
            ]
            print(
                f"Filtered: {len(filtered)}/{len(all_transactions)} transactions")
            return filtered

        return all_transactions
    except Exception as e:
        print(f"_get_uah_transactions error: {e}")
        return []


class AIAnalystView(views.APIView):
    """AI Фінансовий Аналітик"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        question = request.data.get('question', None)

        try:
            bank = BankConnection.objects.filter(
                user=request.user, bank_name='monobank', status='active'
            ).first()

            transactions = []
            if bank:
                transactions = _get_uah_transactions(bank.access_token, days=30)

            result = FinancialAnalystAgent.analyze(transactions, question)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIInvestmentView(views.APIView):
    """AI Інвестиційний Радник"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            bank = BankConnection.objects.filter(
                user=request.user, bank_name='monobank', status='active'
            ).first()

            transactions = []
            balance = 0.0
            if bank:
                transactions = _get_uah_transactions(
                    bank.access_token, days=30)
                balance = _get_real_balance(bank.access_token)[0]

            income = sum(t['amount']
                         for t in transactions if t['type'] == 'income')
            expenses = sum(t['amount']
                           for t in transactions if t['type'] == 'expense')

            bank_data = {
                'balance': balance,
                'income': income,
                'expenses': expenses
            }
            result = InvestmentAdvisorAgent.advise(bank_data)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIForecastView(views.APIView):
    """AI Прогнозист"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        days = int(request.query_params.get('days', 30))

        try:
            bank = BankConnection.objects.filter(
                user=request.user, bank_name='monobank', status='active'
            ).first()

            transactions = []
            if bank:
                transactions = _get_uah_transactions(bank.access_token, days=30)

            result = ForecastAgent.forecast(transactions, days)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIAnomalyView(views.APIView):
    """AI Детектор Аномалій"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            bank = BankConnection.objects.filter(
                user=request.user, bank_name='monobank', status='active'
            ).first()

            transactions = []
            if bank:
                transactions = _get_uah_transactions(bank.access_token, days=30)

            result = AnomalyDetectorAgent.detect(transactions)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIChatView(views.APIView):
    """AI Чат Асистент з персистентною історією в БД"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        message = request.data.get('message', '')

        if not message:
            return Response({'error': 'Повідомлення не може бути порожнім'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bank = BankConnection.objects.filter(
                user=request.user, bank_name='monobank', status='active'
            ).first()

            context = {}
            if bank:
                balance, _ = _get_real_balance(bank.access_token)
                transactions = _get_uah_transactions(bank.access_token, days=30)

                now = datetime.now()
                current_month_income = 0
                current_month_expenses = 0

                for t in transactions:
                    # Внутрішні перекази між рахунками не враховуємо
                    if t.get('type') == 'transfer':
                        continue
                    dt_str = t.get('transaction_date', '')
                    if not dt_str:
                        continue
                    try:
                        t_date = datetime.fromisoformat(dt_str)
                        if t_date.year == now.year and t_date.month == now.month:
                            if t['type'] == 'income':
                                current_month_income += t['amount']
                            elif t['type'] == 'expense':
                                current_month_expenses += t['amount']
                    except ValueError:
                        pass

                context = {
                    'balance': round(balance, 2),
                    'income': round(current_month_income, 2),
                    'expenses': round(current_month_expenses, 2),
                    'month': now.strftime("%B %Y"),
                    'recent_transactions': [
                        {
                            'date': t.get('transaction_date', '')[:10],
                            'type': t.get('type'),
                            'amount': round(t.get('amount', 0), 2),
                            'desc': t.get('description', '')[:30]
                        }
                        for t in transactions[:150]
                    ]
                }

            # Завантажуємо останні 10 повідомлень з БД як контекст для агента
            db_history = list(
                ChatMessage.objects.filter(user=request.user)
                .order_by('-created_at')[:10]
                .values('role', 'text')
            )
            db_history.reverse()  # хронологічний порядок

            result = ChatAgent.chat(message, context, history=db_history)

            # Зберігаємо повідомлення користувача та відповідь агента в БД
            ChatMessage.objects.create(user=request.user, role='user', text=message)
            ChatMessage.objects.create(
                user=request.user,
                role='model',
                text=result.get('response', ''),
                agent=result.get('agent', '')
            )

            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChatHistoryView(views.APIView):
    """Отримати збережену історію чату користувача"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        limit = int(request.query_params.get('limit', 50))
        messages = (
            ChatMessage.objects.filter(user=request.user)
            .order_by('-created_at')[:limit]
            .values('role', 'text', 'agent', 'created_at')
        )
        history = list(reversed(list(messages)))
        return Response({'history': history})

    def delete(self, request):
        """Очистити всю історію чату"""
        ChatMessage.objects.filter(user=request.user).delete()
        return Response({'status': 'Історію чату очищено'})
