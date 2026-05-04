from rest_framework import serializers
from .models import (
    BankConnection, CryptoExchange, Transaction,
    TransactionCategory, FinancialForecast, SyncLog
)


class BankConnectionSerializer(serializers.ModelSerializer):
    """Serializer для підключень до банків"""
    
    class Meta:
        model = BankConnection
        fields = ('id', 'name', 'bank_name', 'status', 'account_name', 'last_sync', 'created_at')
        read_only_fields = ('id', 'status', 'last_sync', 'created_at')


class AddBankConnectionSerializer(serializers.Serializer):
    """Serializer для додавання підключення до банку"""
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    bank_name = serializers.ChoiceField(choices=[('monobank', 'Monobank'), ('pumb', 'ПУМБ')])
    access_token = serializers.CharField(write_only=True)


class CryptoExchangeSerializer(serializers.ModelSerializer):
    """Serializer для підключень до бірж"""
    
    class Meta:
        model = CryptoExchange
        fields = ('id', 'exchange_name', 'status', 'account_name', 'last_sync', 'created_at')
        read_only_fields = ('id', 'status', 'last_sync', 'created_at')


class AddCryptoExchangeSerializer(serializers.Serializer):
    """Serializer для додавання підключення до біржі"""
    exchange_name = serializers.ChoiceField(
        choices=[('binance', 'Binance'), ('bybit', 'Bybit'), ('okx', 'OKX')]
    )
    api_key = serializers.CharField(write_only=True)
    api_secret = serializers.CharField(write_only=True)
    api_passphrase = serializers.CharField(write_only=True, required=False, allow_blank=True)


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer для категорій транзакцій"""
    
    class Meta:
        model = TransactionCategory
        fields = ('id', 'name', 'type', 'icon', 'color', 'is_system')
        read_only_fields = ('id', 'is_system')


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer для транзакцій"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'source', 'type', 'category', 'category_name',
            'amount', 'currency', 'description', 'counterparty',
            'transaction_date', 'created_at'
        )
        read_only_fields = ('id', 'source', 'created_at')


class FinancialForecastSerializer(serializers.ModelSerializer):
    """Serializer для прогнозів"""
    
    class Meta:
        model = FinancialForecast
        fields = (
            'id', 'forecast_type', 'period_start', 'period_end',
            'predicted_value', 'currency', 'confidence_score',
            'model_used', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class SyncLogSerializer(serializers.ModelSerializer):
    """Serializer для логів синхронізації"""
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = SyncLog
        fields = (
            'id', 'source', 'status', 'transactions_added',
            'transactions_updated', 'error_message',
            'started_at', 'completed_at', 'duration'
        )
        read_only_fields = fields
    
    def get_duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return delta.total_seconds()
        return None


class SyncRequestSerializer(serializers.Serializer):
    """Serializer для запиту синхронізації"""
    source = serializers.CharField()
    days = serializers.IntegerField(default=30, min_value=1, max_value=365, required=False)
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
