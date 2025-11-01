from django.urls import path
from .views import (
    BankConnectionListView, AddBankConnectionView, DeleteBankConnectionView,
    CryptoExchangeListView, AddCryptoExchangeView, DeleteCryptoExchangeView,
    TransactionListView, SyncView, SyncLogListView, TransactionCategoryListView,
    PUMBAuthInitView, PUMBAuthCallbackView
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
    
    # Transactions
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/sync/', SyncView.as_view(), name='transaction_sync'),
    
    # Categories
    path('categories/', TransactionCategoryListView.as_view(), name='category_list'),
    
    # Sync logs
    path('sync-logs/', SyncLogListView.as_view(), name='sync_log_list'),
]
