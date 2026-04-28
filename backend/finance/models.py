from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class EncryptedField(models.TextField):
    """Custom field для шифрування чутливих даних"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Генеруємо ключ шифрування з SECRET_KEY
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        self.cipher = Fernet(key)
    
    def get_prep_value(self, value):
        if value is None:
            return value
        # Шифруємо перед збереженням в БД
        return self.cipher.encrypt(value.encode()).decode()
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        # Розшифровуємо при читанні з БД
        return self.cipher.decrypt(value.encode()).decode()
    
    def to_python(self, value):
        if isinstance(value, str) or value is None:
            return value
        return str(value)


class UserProfile(models.Model):
    """Розширений профіль користувача"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    currency_preference = models.CharField(max_length=3, default='UAH')
    timezone = models.CharField(max_length=50, default='Europe/Kiev')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile: {self.user.username}"


class BankConnection(models.Model):
    """Підключення до банків"""
    BANK_CHOICES = [
        ('monobank', 'Monobank'),
        ('pumb', 'ПУМБ'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активне'),
        ('inactive', 'Неактивне'),
        ('error', 'Помилка'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_connections')
    name = models.CharField(max_length=255, blank=True, null=True)  # Назва підключення (наприклад: "Мій Monobank")
    bank_name = models.CharField(max_length=50, choices=BANK_CHOICES)
    
    # Зашифровані токени
    access_token = EncryptedField()
    refresh_token = EncryptedField(blank=True, null=True)
    
    # Метадані
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    account_name = models.CharField(max_length=255, blank=True, null=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bank_connections'
        unique_together = ['user', 'bank_name']
        verbose_name = 'Bank Connection'
        verbose_name_plural = 'Bank Connections'
    
    def __str__(self):
        return f"{self.user.username} - {self.name or self.bank_name}"


class CryptoExchange(models.Model):
    """Підключення до криптовалютних бірж"""
    EXCHANGE_CHOICES = [
        ('binance', 'Binance'),
        ('bybit', 'Bybit'),
        ('okx', 'OKX'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активне'),
        ('inactive', 'Неактивне'),
        ('error', 'Помилка'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crypto_exchanges')
    exchange_name = models.CharField(max_length=50, choices=EXCHANGE_CHOICES)
    
    # Зашифровані API ключі
    api_key = EncryptedField()
    api_secret = EncryptedField()
    api_passphrase = EncryptedField(blank=True, null=True)  # Для OKX
    
    # Метадані
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    account_name = models.CharField(max_length=255, blank=True, null=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_exchanges'
        unique_together = ['user', 'exchange_name']
        verbose_name = 'Crypto Exchange'
        verbose_name_plural = 'Crypto Exchanges'
    
    def __str__(self):
        return f"{self.user.username} - {self.exchange_name}"


class TransactionCategory(models.Model):
    """Категорії транзакцій"""
    CATEGORY_TYPES = [
        ('income', 'Дохід'),
        ('expense', 'Витрата'),
        ('transfer', 'Переказ'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=7, default='#000000')
    is_system = models.BooleanField(default=False)  # Системна або створена користувачем
    
    class Meta:
        db_table = 'transaction_categories'
        verbose_name = 'Transaction Category'
        verbose_name_plural = 'Transaction Categories'
    
    def __str__(self):
        return f"{self.name} ({self.type})"


class Transaction(models.Model):
    """Транзакції з банків та бірж"""
    SOURCE_CHOICES = [
        ('monobank', 'Monobank'),
        ('pumb', 'ПУМБ'),
        ('binance', 'Binance'),
        ('bybit', 'Bybit'),
        ('okx', 'OKX'),
        ('manual', 'Вручну'),
    ]
    
    TYPE_CHOICES = [
        ('income', 'Дохід'),
        ('expense', 'Витрата'),
        ('transfer', 'Переказ'),
        ('trade', 'Торгівля'),
        ('deposit', 'Депозит'),
        ('withdrawal', 'Виведення'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    
    # Джерело
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    source_id = models.CharField(max_length=255)  # ID з API банку/біржі
    
    # Деталі транзакції
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10)
    
    # Додаткова інформація
    description = models.TextField(blank=True, null=True)
    counterparty = models.CharField(max_length=255, blank=True, null=True)
    
    # Дати
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Метадані
    raw_data = models.JSONField(blank=True, null=True)  # Повні дані з API
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['user', 'transaction_date']),
            models.Index(fields=['source', 'source_id']),
        ]
        unique_together = ['source', 'source_id']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} ({self.transaction_date})"


class FinancialForecast(models.Model):
    """Прогнози фінансових показників"""
    FORECAST_TYPES = [
        ('income', 'Прогноз доходів'),
        ('expense', 'Прогноз витрат'),
        ('balance', 'Прогноз балансу'),
        ('crypto', 'Прогноз крипто'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forecasts')
    
    forecast_type = models.CharField(max_length=20, choices=FORECAST_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    predicted_value = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=10)
    
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text='0-100')
    
    # Метадані
    model_used = models.CharField(max_length=50, blank=True, null=True)
    parameters = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'financial_forecasts'
        indexes = [
            models.Index(fields=['user', 'period_start', 'period_end']),
        ]
        verbose_name = 'Financial Forecast'
        verbose_name_plural = 'Financial Forecasts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.forecast_type} ({self.period_start} - {self.period_end})"


class ChatMessage(models.Model):
    """Збережені повідомлення чату з AI-асистентом"""
    ROLE_CHOICES = [
        ('user', 'Користувач'),
        ('model', 'AI Асистент'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    text = models.TextField()
    agent = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"{self.user.username} [{self.role}]: {self.text[:50]}"


class SyncLog(models.Model):
    """Лог синхронізації з банками та біржами"""
    STATUS_CHOICES = [
        ('success', 'Успішно'),
        ('partial', 'Частково'),
        ('failed', 'Помилка'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sync_logs')
    source = models.CharField(max_length=50)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    transactions_added = models.IntegerField(default=0)
    transactions_updated = models.IntegerField(default=0)
    
    error_message = models.TextField(blank=True, null=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'sync_logs'
        verbose_name = 'Sync Log'
        verbose_name_plural = 'Sync Logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.source} - {self.status}"
