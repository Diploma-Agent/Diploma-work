from django.urls import path
from .views import (
    BankConnectionListView, AddBankConnectionView, DeleteBankConnectionView,
    CryptoExchangeListView, AddCryptoExchangeView, DeleteCryptoExchangeView,
    TransactionListView, SyncView, SyncLogListView, TransactionCategoryListView,
    PUMBAuthInitView, PUMBAuthCallbackView,
    ExchangeBalanceView, ExchangeOrdersView, BankAnalyticsView,
    AIAnalystView, AIInvestmentView, AIForecastView, AIAnomalyView, AIChatView,
    ChatHistoryView
)

app_name = 'finance'

urlpatterns = [
    # Bank connections
    path('banks/', BankConnectionListView.as_view(), name='bank_list'),
    path('banks/add/', AddBankConnectionView.as_view(), name='bank_add'),
    path('banks/<int:pk>/delete/', DeleteBankConnectionView.as_view(), name='bank_delete'),
    
    # PUMB OAuth2
    path('pumb/auth/', PUMBAuthInitView.as_view(), name='pumb_auth_init'),
    path('pumb/callback/', PUMBAuthCallbackView.as_view(), name='pumb_callback'),
    
    # Crypto exchanges
    path('exchanges/', CryptoExchangeListView.as_view(), name='exchange_list'),
    path('exchanges/add/', AddCryptoExchangeView.as_view(), name='exchange_add'),
    path('exchanges/<int:pk>/delete/', DeleteCryptoExchangeView.as_view(), name='exchange_delete'),
    
    # Exchange info
    path('exchanges/balance/', ExchangeBalanceView.as_view(), name='exchange_balance'),
    path('exchanges/orders/', ExchangeOrdersView.as_view(), name='exchange_orders'),
    
    # Transactions
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/sync/', SyncView.as_view(), name='transaction_sync'),
    
    # Categories
    path('categories/', TransactionCategoryListView.as_view(), name='category_list'),
    
    # Sync logs
    path('sync-logs/', SyncLogListView.as_view(), name='sync_log_list'),
    
    # Analytics
    path('analytics/bank/', BankAnalyticsView.as_view(), name='bank_analytics'),
    
    # AI Agents
    path('ai/analyst/', AIAnalystView.as_view(), name='ai_analyst'),
    path('ai/investment/', AIInvestmentView.as_view(), name='ai_investment'),
    path('ai/forecast/', AIForecastView.as_view(), name='ai_forecast'),
    path('ai/anomaly/', AIAnomalyView.as_view(), name='ai_anomaly'),
    path('ai/chat/', AIChatView.as_view(), name='ai_chat'),
    path('ai/chat/history/', ChatHistoryView.as_view(), name='ai_chat_history'),
]
