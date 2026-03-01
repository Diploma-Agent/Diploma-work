from google import genai
from google.genai import types
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import re
from django.conf import settings

# Шлях до credentials файлу
credentials_file = os.environ.get('GOOGLE_CREDENTIALS') or getattr(settings, 'GOOGLE_CREDENTIALS', None)
if credentials_file and not os.path.isabs(credentials_file):
    base_dir = str(getattr(settings, 'BASE_DIR', ''))
    credentials_file = os.path.join(base_dir, credentials_file)

if not credentials_file or not os.path.exists(credentials_file):
    raise ValueError(f"Google credentials файл не знайдено: {credentials_file}")

# Service Account credentials для Generative Language API
credentials = service_account.Credentials.from_service_account_file(
    credentials_file,
    scopes=[
        'https://www.googleapis.com/auth/generative-language',
        'https://www.googleapis.com/auth/cloud-platform',
    ]
)

# Оновлюємо токен
credentials.refresh(Request())

client = genai.Client(
    http_options={'api_version': 'v1beta'},
    credentials=credentials,
)

MODELS = [
    'gemini-2.5-flash-preview-05-20',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
]
MODEL = MODELS[0]


def generate_with_retry(contents, config=None, max_retries=1):
    """Виклик Gemini API через Google Service Account Credentials"""
    last_error = None
    for model in MODELS:
        try:
            kwargs = {'model': model, 'contents': contents}
            if config:
                kwargs['config'] = config
            response = client.models.generate_content(**kwargs)
            if model != MODELS[0]:
                print(f"[Gemini] Використано модель: {model}")
            return response
        except Exception as e:
            error_str = str(e)
            last_error = error_str
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                print(f"[Gemini] {model} — ліміт, переходимо далі...")
                continue
            elif 'not found' in error_str.lower() or '404' in error_str:
                print(f"[Gemini] {model} не знайдена, пробуємо наступну...")
                continue
            else:
                raise e
    raise Exception(f"Всі моделі недоступні. Помилка: {last_error}")
