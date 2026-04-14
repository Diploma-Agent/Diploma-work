from google import genai
from google.genai import types
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import re
from django.conf import settings

# Шлях до credentials файлу
credentials_file = os.environ.get('GOOGLE_CREDENTIALS') or getattr(
    settings, 'GOOGLE_CREDENTIALS', None)
if credentials_file and not os.path.isabs(credentials_file):
    base_dir = str(getattr(settings, 'BASE_DIR', ''))
    credentials_file = os.path.join(base_dir, credentials_file)

if not credentials_file or not os.path.exists(credentials_file):
    raise ValueError(
        f"Google credentials файл не знайдено: {credentials_file}")

# Service Account credentials
credentials = service_account.Credentials.from_service_account_file(
    credentials_file,
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

# Налаштовуємо Gemini з credentials (новий SDK)
# Зверніть увагу: ми використовуємо `credentials`, якщо вони визначені,
# але новий клієнт іншим способом передає їх в API або використовує APPLICATION_DEFAULT_CREDENTIALS.
# Для genai.Client можна спробувати ініціалізацію з `credentials=credentials`
# Якщо не підтримується, можливо доведеться встановити змінну середовища GOOGLE_APPLICATION_CREDENTIALS
client = genai.Client(credentials=credentials)

MODELS = [
    'gemini-3-flash-preview',
    'gemini-2.5-flash-preview-05-20',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
]
MODEL = MODELS[0]


def generate_with_retry(contents, config=None, max_retries=1, system_instruction=None, tools=None):
    """Виклик Gemini API через Google Service Account Credentials (новий SDK `google-genai`)"""
    last_error = None

    # Формуємо конфігурацію для нового SDK
    gen_config_kwargs = {}
    if config:
        # Перенос старих параметрів (якщо вони були передані як dict)
        if isinstance(config, dict):
            # Наприклад, temperature, top_k
            for k, v in config.items():
                gen_config_kwargs[k] = v
        else:
            # Якщо config вже об'єкт старого GenerationConfig
            pass  # треба адаптувати під ваші потреби

    if system_instruction:
        gen_config_kwargs['system_instruction'] = system_instruction
    if tools:
        gen_config_kwargs['tools'] = tools

    # Створюємо об'єкт конфігурації
    final_config = types.GenerateContentConfig(
        **gen_config_kwargs) if gen_config_kwargs else None

    for model_name in MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=final_config
            )
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
                print(
                    f"[Gemini] {model_name} не знайдена, пробуємо наступну...")
                continue
            else:
                raise e
    raise Exception(f"Всі моделі недоступні. Помилка: {last_error}")
