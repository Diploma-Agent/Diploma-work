from annotated_types import doc
from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import traceback
import secrets
import pytz
from datetime import datetime, date, timedelta, timezone as dt_timezone
from django.utils import timezone
from django.conf import settings
from pymongo import MongoClient
import re

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
from .tasks import sync_user_connection


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

        # Запускаємо початкову синхронізацію у фоні через Celery
        try:
            sync_user_connection.delay(request.user.id, bank_name, bank_connection.id)
        except Exception:
            pass  # Celery може бути недоступний — не блокуємо відповідь

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

        # Запускаємо початкову синхронізацію у фоні через Celery
        try:
            sync_user_connection.delay(request.user.id, exchange_name, exchange.id)
        except Exception:
            pass  # Celery може бути недоступний — не блокуємо відповідь

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
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        source = request.query_params.get('source', 'all')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # 1. Починаємо з усіх транзакцій користувача
        queryset = Transaction.objects.filter(user=request.user)

        # 2. Якщо клієнт передав дати, фільтруємо по них
        if date_from and date_to:
            # Додаємо час до date_to, щоб захопити весь останній день включно
            queryset = queryset.filter(
                transaction_date__gte=date_from,
                transaction_date__lte=f"{date_to}T23:59:59"
            )
        # 3. Якщо дат немає, працює дефолтна логіка (останні 30 днів)
        else:
            days = int(request.query_params.get('days', 30))
            limit_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(transaction_date__gte=limit_date)
        
        # 4. Фільтр по джерелу
        if source != 'all':
            queryset = queryset.filter(source=source)
            
        transactions = queryset.order_by('-transaction_date')
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response(serializer.data)


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
        date_from = serializer.validated_data.get('date_from')
        date_to = serializer.validated_data.get('date_to')

        try:
            if source == 'monobank':
                connection = BankConnection.objects.get(
                    user=request.user,
                    bank_name='monobank'
                )
                service = MonobankService(request.user)
                result = service.sync_transactions(connection, days=days, date_from=date_from, date_to=date_to)
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

                # Отримуємо поточні ціни всіх пар до USDT (публічний endpoint, без підпису)
                prices = {}
                try:
                    import requests as req
                    price_resp = req.get(
                        'https://api.binance.com/api/v3/ticker/price',
                        timeout=5
                    ).json()
                    for p in price_resp:
                        symbol = p.get('symbol', '')
                        if symbol.endswith('USDT'):
                            asset = symbol[:-4]  # 'BTCUSDT' → 'BTC'
                            prices[asset] = float(p.get('price', 0))
                    prices['USDT'] = 1.0
                    prices['BUSD'] = 1.0
                    prices['USDC'] = 1.0
                except Exception:
                    pass

                coins = []
                total_equity = 0.0
                for b in raw_balance:
                    asset = b.get('asset', '')
                    free = float(b.get('free', 0))
                    locked = float(b.get('locked', 0))
                    bal = free + locked
                    if bal <= 0:
                        continue
                    usd_price = prices.get(asset, 0)
                    usd_value = round(bal * usd_price, 4)
                    total_equity += usd_value
                    coins.append({
                        'coin': asset,
                        'walletBalance': str(bal),
                        'usdValue': str(usd_value)
                    })

                formatted = {
                    'list': [{
                        'totalEquity': str(round(total_equity, 2)),
                        'coin': coins
                    }]
                }
                return Response(formatted)

            # Тут можна додати інші біржі

            return Response({'error': 'Біржа не підтримується'}, status=status.HTTP_400_BAD_REQUEST)

        except CryptoExchange.DoesNotExist:
            # Підключення не знайдено — повертаємо порожній баланс (не 404, щоб фронтенд не ламався)
            return Response({
                'list': [{'totalEquity': '0', 'coin': []}],
                'available': False,
                'error': 'Підключення не знайдено'
            })
        except Exception as e:
            # Будь-яка помилка API (невірний ключ, немає прав) — порожній баланс
            print(f"[ExchangeBalance] {exchange_name} error: {e}")
            return Response({
                'list': [{'totalEquity': '0', 'coin': []}],
                'available': False,
                'error': str(e)
            })


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

            return Response({'list': [], 'available': False, 'error': 'Біржа не підтримується'})

        except CryptoExchange.DoesNotExist:
            return Response({'list': [], 'available': False, 'error': 'Підключення не знайдено'})
        except Exception as e:
            # Futures можуть бути недоступні (немає прав або не торгується) — не 400, а порожній список
            print(f"[ExchangeOrders] {exchange_name}/{category} error: {e}")
            return Response({'list': [], 'available': False, 'error': str(e)})


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
            # Баланс — з Monobank API (реальний поточний баланс рахунку)
            balance = 0.0
            bank = BankConnection.objects.filter(
                user=request.user, bank_name='monobank', status='active'
            ).first()
            if bank:
                try:
                    balance = _get_real_balance(bank.access_token)[0]
                except Exception:
                    pass

            # Доходи/витрати — з БД (повна локальна картина, без rate-limit)
            income = 0.0
            expenses = 0.0
            try:
                dt_to = datetime.now(pytz.utc)
                dt_from = dt_to - timedelta(days=30)
                client = MongoClient(settings.MONGODB_URI)
                db_mongo = client[settings.MONGODB_DATABASE]
                for doc in db_mongo['transactions'].find({
                    'user_id': request.user.id,
                    'currency': 'UAH',
                    'type': {'$in': ['income', 'expense']},
                    'transaction_date': {'$gte': dt_from, '$lte': dt_to}
                }):
                    amt = float(str(doc.get('amount', 0)))
                    if doc.get('type') == 'income':
                        income += amt
                    else:
                        expenses += amt
                client.close()
            except Exception as db_err:
                print(f"[AIInvestmentView] DB error: {db_err}")

            bank_data = {
                'balance': round(balance, 2),
                'income': round(income, 2),
                'expenses': round(expenses, 2),
            }
            result = InvestmentAdvisorAgent.advise(bank_data)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIForecastView(views.APIView):
    """AI Прогнозист"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        from django.core.cache import cache
        import hashlib
        import json

        days = int(request.query_params.get('days', 30))

        try:
            # Беремо транзакції з БД за останні 180 днів (6 міс) для якісного тренду.
            # НЕ звертаємось до Monobank API — щоб не впиратись у rate limit
            # і отримувати повну збережену історію.
            transactions = []
            try:
                dt_to = datetime.now(pytz.utc)
                dt_from = dt_to - timedelta(days=180)

                client = MongoClient(settings.MONGODB_URI)
                db_mongo = client[settings.MONGODB_DATABASE]
                collection = db_mongo['transactions']

                query = {
                    'user_id': request.user.id,
                    'currency': 'UAH',
                    'type': {'$in': ['income', 'expense']},
                    'transaction_date': {'$gte': dt_from, '$lte': dt_to}
                }
                cursor = collection.find(query).sort('transaction_date', 1)

                for doc in cursor:
                    tx_date = doc.get('transaction_date', dt_to)
                    tx_date_iso = tx_date.isoformat() if hasattr(tx_date, 'isoformat') else str(tx_date)
                    transactions.append({
                        'transaction_date': tx_date_iso,
                        'type': doc.get('type', ''),
                        'amount': float(str(doc.get('amount', 0))),
                        'id': str(doc.get('_id', '')),
                    })
                client.close()
                print(f"[AIForecastView] Отримано {len(transactions)} транзакцій із БД за 180 днів")
            except Exception as db_err:
                print(f"[AIForecastView] DB error, fallback to Monobank API: {db_err}")
                bank = BankConnection.objects.filter(
                    user=request.user, bank_name='monobank', status='active'
                ).first()
                if bank:
                    transactions = _get_uah_transactions(bank.access_token, days=90)
            
            # Створюємо хеш на основі транзакцій та днів, щоб перевірити, чи змінились дані
            tx_light = [{'id': t.get('id'), 'amount': t.get('amount')} for t in transactions]
            cache_string = json.dumps({'user': request.user.id, 'days': days, 'tx': tx_light}, sort_keys=True)
            cache_hash = hashlib.md5(cache_string.encode('utf-8')).hexdigest()
            cache_key = f'ai_forecast_{request.user.id}_{cache_hash}'
            
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)

            result = ForecastAgent.forecast(transactions, days)

            # Зберігаємо прогноз в БД
            if 'data' in result:
                d = result['data']
                today = date.today()
                period_end = today + timedelta(days=days)

                def r2_to_confidence(metrics):
                    r2 = (metrics or {}).get('r2')
                    if r2 is None:
                        return 50.0
                    return round(max(0.0, min(100.0, float(r2) * 100)), 2)

                exp_conf = r2_to_confidence(d['accuracy']['expenses'])
                inc_conf = r2_to_confidence(d['accuracy']['income'])

                FinancialForecast.objects.create(
                    user=request.user,
                    forecast_type='expense',
                    period_start=today,
                    period_end=period_end,
                    predicted_value=d['forecast_expense'],
                    currency='UAH',
                    confidence_score=exp_conf,
                    model_used='linear_regression',
                    parameters=d,
                )
                FinancialForecast.objects.create(
                    user=request.user,
                    forecast_type='income',
                    period_start=today,
                    period_end=period_end,
                    predicted_value=d['forecast_income'],
                    currency='UAH',
                    confidence_score=inc_conf,
                    model_used='linear_regression',
                    parameters=d,
                )
                FinancialForecast.objects.create(
                    user=request.user,
                    forecast_type='balance',
                    period_start=today,
                    period_end=period_end,
                    predicted_value=d['forecast_balance'],
                    currency='UAH',
                    confidence_score=round((exp_conf + inc_conf) / 2, 2),
                    model_used='linear_regression',
                    parameters=d,
                )
                
                # Зберігаємо результат в кеш на 24 години (якщо транзакції не зміняться)
                cache.set(cache_key, result, 60 * 60 * 24)

            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AIAnomalyView(views.APIView):
    """AI Детектор Аномалій"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            # 90 днів з БД — більший вибір дає точнішу медіану і MAD-поріг
            transactions = []
            try:
                dt_to = datetime.now(pytz.utc)
                dt_from = dt_to - timedelta(days=90)
                client = MongoClient(settings.MONGODB_URI)
                db_mongo = client[settings.MONGODB_DATABASE]
                for doc in db_mongo['transactions'].find({
                    'user_id': request.user.id,
                    'currency': 'UAH',
                    'type': {'$in': ['income', 'expense']},
                    'transaction_date': {'$gte': dt_from, '$lte': dt_to}
                }).sort('transaction_date', -1):
                    tx_date = doc.get('transaction_date', dt_to)
                    transactions.append({
                        'type': doc.get('type', ''),
                        'amount': float(str(doc.get('amount', 0))),
                        'description': doc.get('description', ''),
                        'counterparty': doc.get('counterparty', ''),
                        'transaction_date': (
                            tx_date.isoformat()
                            if hasattr(tx_date, 'isoformat') else str(tx_date)
                        ),
                    })
                client.close()
                print(f"[AIAnomalyView] {len(transactions)} транзакцій за 90 днів з БД")
            except Exception as db_err:
                print(f"[AIAnomalyView] DB error: {db_err}")

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
                try:
                    balance, _ = _get_real_balance(bank.access_token)
                except Exception:
                    balance = 0

                from django.utils import timezone
                now = timezone.now()
                thirty_days_ago = now - timedelta(days=30)

                # БЕРЕМО ДАНІ ВИКЛЮЧНО З ЛОКАЛЬНОЇ БАЗИ MongoDB
                # Фільтруємо тільки UAH-транзакції (банк), щоб не змішувати з крипто
                local_txs = Transaction.objects.filter(
                    user=request.user,
                    transaction_date__gte=thirty_days_ago,
                    currency='UAH'
                ).exclude(type='transfer').order_by('-transaction_date')

                # Баг 1 fix: підсумок і список тепер охоплюють однаковий період (30 днів)
                # Баг 2 fix: transfer-транзакції виключені через .exclude() — не потраплять ні в підсумок, ні в список
                income_30d = 0
                expenses_30d = 0

                for t in local_txs:
                    if t.type == 'income':
                        income_30d += float(str(t.amount))
                    elif t.type == 'expense':
                        expenses_30d += float(str(t.amount))

                # Швидка детекція аномалій для контексту чату
                # (використовуємо вже отримані local_txs, без зайвого API-виклику)
                tx_for_anomaly = [
                    {
                        'type': t.type,
                        'amount': round(float(str(t.amount)), 2),
                        'description': t.description,
                        'counterparty': getattr(t, 'counterparty', ''),
                        'transaction_date': t.transaction_date.isoformat(),
                    }
                    for t in local_txs
                ]
                try:
                    anomaly_result = AnomalyDetectorAgent.detect(tx_for_anomaly)
                    anomaly_count = anomaly_result.get('anomaly_count', 0)
                    anomalous_txs = anomaly_result.get('anomalous_transactions', [])
                except Exception:
                    anomaly_count = 0
                    anomalous_txs = []

                context = {
                    'balance': round(balance, 2),
                    'income': round(income_30d, 2),
                    'expenses': round(expenses_30d, 2),
                    'month': now.strftime("%B %Y"),
                    'anomaly_count': anomaly_count,
                    'anomalous_transactions': anomalous_txs,
                    'recent_transactions': [
                        {
                            'date': t.transaction_date.isoformat()[:10],
                            'type': t.type,
                            'amount': round(float(str(t.amount)), 2),
                            'desc': t.description[:30]
                        }
                        for t in local_txs
                    ]
                }

            # Завантажуємо останні 10 повідомлень з БД як контекст для агента
            db_history = list(
                ChatMessage.objects.filter(user=request.user)
                .order_by('-created_at')[:10]
                .values('role', 'text')
            )
            db_history.reverse()  # хронологічний порядок
            
            def fetch_tx_callback(days=30, date_from=None, date_to=None):
                print(f"[fetch_tx_callback] days={days}, date_from={date_from}, date_to={date_to}")

                # Часовий пояс Kyiv — саме в ньому Monobank показує транзакції
                kyiv_tz = pytz.timezone('Europe/Kiev')

                def parse_date_kyiv(date_str, is_end=False):
                    """Парсить рядок дати як Kyiv-aware datetime і конвертує в UTC."""
                    try:
                        dt_naive = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        try:
                            dt_naive = datetime.strptime(date_str, "%Y-%m")
                            if is_end:
                                # Останній день місяця
                                if dt_naive.month == 12:
                                    dt_naive = dt_naive.replace(year=dt_naive.year + 1, month=1, day=1) - timedelta(days=1)
                                else:
                                    dt_naive = dt_naive.replace(month=dt_naive.month + 1, day=1) - timedelta(days=1)
                        except ValueError:
                            dt_naive = timezone.now()

                    if is_end:
                        dt_naive = dt_naive.replace(hour=23, minute=59, second=59)

                    # Локалізуємо як Kyiv і конвертуємо в UTC
                    return kyiv_tz.localize(dt_naive).astimezone(pytz.utc)

                try:
                    # Визначаємо діапазон дат у UTC (з урахуванням Kyiv-timezone)
                    if date_from and date_from not in ("None", "null") and \
                    date_to and date_to not in ("None", "null"):
                        if isinstance(date_from, str):
                            dt_from = parse_date_kyiv(date_from, is_end=False)
                        else:
                            dt_from = kyiv_tz.localize(datetime.combine(date_from, datetime.min.time())).astimezone(pytz.utc)

                        if isinstance(date_to, str):
                            dt_to = parse_date_kyiv(date_to, is_end=True)
                        else:
                            dt_to = kyiv_tz.localize(datetime.combine(date_to, datetime.max.time())).astimezone(pytz.utc)
                    else:
                        dt_to = datetime.now(pytz.utc)
                        dt_from = dt_to - timedelta(days=days)

                    # Підключаємось до MongoDB напряму
                    client = MongoClient(settings.MONGODB_URI)
                    db = client[settings.MONGODB_DATABASE]
                    collection = db['transactions']

                    # Фільтруємо тільки UAH-транзакції, без переказів.
                    # dt_from / dt_to — UTC-aware datetimes, що відповідають Kyiv-добам
                    query = {
                        'user_id': request.user.id,
                        'currency': 'UAH',
                        'type': {'$in': ['income', 'expense']},
                        'transaction_date': {
                            '$gte': dt_from,
                            '$lte': dt_to
                        }
                    }

                    cursor = collection.find(query).sort('transaction_date', -1)

                    result = []
                    income_total = 0.0
                    expense_total = 0.0
                    for doc in cursor:
                        tx_date = doc.get('transaction_date', datetime.now(pytz.utc))
                        tx_date_iso = tx_date.isoformat() if hasattr(tx_date, 'isoformat') else str(tx_date)
                        amount = float(str(doc.get('amount', 0)))
                        tx_type = doc.get('type', '')

                        if tx_type == 'income':
                            income_total += amount
                        elif tx_type == 'expense':
                            expense_total += amount

                        result.append({
                            'transaction_date': tx_date_iso,
                            'type': tx_type,
                            'amount': amount,
                            'description': doc.get('description', ''),
                        })

                    client.close()
                    print(f"[PyMongo] Знайдено {len(result)} транзакцій | "
                          f"Діапазон UTC: {dt_from.isoformat()} — {dt_to.isoformat()} | "
                          f"Надходження: {income_total:.2f} UAH | Витрати: {expense_total:.2f} UAH")
                    return result

                except Exception as e:
                    print(f"Помилка PyMongo у fetch_tx_callback: {e}")
                    import traceback
                    print(traceback.format_exc())
                    return []

            result = ChatAgent.chat(message, context, history=db_history, fetch_transactions_cb=fetch_tx_callback)

            # Зберігаємо повідомлення користувача та відповідь агента в БД
            ChatMessage.objects.create(user=request.user, role='user', text=message)
            ChatMessage.objects.create(
                user=request.user,
                role='model',
                text=result.get('response', ''),
                agent=result.get('agent', '')
            )

            return Response(result)
        
        except ValueError as ve:
            # Ловимо наші валідаційні помилки (наприклад, 400 від Gemini)
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as re:
            # Ловимо помилки після вичерпання спроб ретраю (наприклад, Gemini лежить)
            return Response({'error': 'Штучний інтелект наразі перевантажений. Спробуйте пізніше.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            # Лобальний відловник для всіх інших неочікуваних помилок (щоб сервер не падав)
            import traceback
            full_trace = traceback.format_exc()
            print(f"КРИТИЧНА ПОМИЛКА ЧАТУ:\n{full_trace}") # Виведе в консоль повний трейс для дебагу
            return Response(
                {'error': 'Виникла внутрішня помилка під час обробки вашого запиту.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
