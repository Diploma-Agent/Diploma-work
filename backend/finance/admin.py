from django.contrib import admin
from .models import (
    UserProfile, BankConnection, CryptoExchange,
    Transaction, TransactionCategory, FinancialForecast, SyncLog
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency_preference', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(BankConnection)
class BankConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank_name', 'status', 'last_sync', 'created_at')
    list_filter = ('bank_name', 'status')
    search_fields = ('user__username', 'account_name')


@admin.register(CryptoExchange)
class CryptoExchangeAdmin(admin.ModelAdmin):
    list_display = ('user', 'exchange_name', 'status', 'last_sync', 'created_at')
    list_filter = ('exchange_name', 'status')
    search_fields = ('user__username', 'account_name')


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_system')
    list_filter = ('type', 'is_system')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'source', 'type', 'amount', 'currency', 'transaction_date')
    list_filter = ('source', 'type', 'currency')
    search_fields = ('user__username', 'description', 'counterparty')
    date_hierarchy = 'transaction_date'


@admin.register(FinancialForecast)
class FinancialForecastAdmin(admin.ModelAdmin):
    list_display = ('user', 'forecast_type', 'predicted_value', 'confidence_score', 'created_at')
    list_filter = ('forecast_type',)


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'source', 'status', 'transactions_added', 'started_at', 'completed_at')
    list_filter = ('source', 'status')
    date_hierarchy = 'started_at'
