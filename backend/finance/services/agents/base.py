import google.generativeai as genai
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

# Service Account credentials
credentials = service_account.Credentials.from_service_account_file(
    credentials_file,
    scopes=['https://www.googleapis.com/auth/generative-language.retriever']
)

# Налаштовуємо Gemini з credentials
genai.configure(credentials=credentials)

MODELS = [
    'gemini-3-flash-preview',
    'gemini-2.5-flash-preview-05-20',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
]
MODEL = MODELS[0]


def generate_with_retry(contents, config=None, max_retries=1, system_instruction=None):
    """Виклик Gemini API через Google Service Account Credentials (старий SDK)"""
    last_error = None
    for model_name in MODELS:
        try:
            model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
            kwargs = {'contents': contents}
            if config:
                kwargs['generation_config'] = config
            response = model.generate_content(**kwargs)
            if model_name != MODELS[0]:
                print(f"[Gemini] Використано модель: {model_name}")
            return response
        except Exception as e:
            error_str = str(e)
            last_error = error_str
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                print(f"[Gemini] {model_name} — ліміт, переходимо далі...")
                continue
            elif 'not found' in error_str.lower() or '404' in error_str:
                print(f"[Gemini] {model_name} не знайдена, пробуємо наступну...")
                continue
            else:
                raise e
    raise Exception(f"Всі моделі недоступні. Помилка: {last_error}")
