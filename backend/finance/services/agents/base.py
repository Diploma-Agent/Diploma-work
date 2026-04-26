import google.generativeai as genai
from google.oauth2 import service_account
import os
import time
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
    scopes=['https://www.googleapis.com/auth/generative-language.retriever']
)

genai.configure(credentials=credentials)

MODELS = [
    'gemini-3-flash-preview',
    'gemini-2.5-flash-preview-05-20',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
    'gemini-pro'
]
MODEL = MODELS[0]


def generate_with_retry(contents, config=None, max_retries=3, system_instruction=None, tools=None):
    """Виклик Gemini API через Google Service Account Credentials з Exponential Backoff"""
    last_error = None

    if config and isinstance(config, dict):
        config = genai.types.GenerationConfig(**config)

    for attempt in range(max_retries):
        for model_name in MODELS:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction,
                    tools=tools
                )

                kwargs = {'contents': contents}
                if config:
                    kwargs['generation_config'] = config

                response = model.generate_content(
                    **kwargs,
                    # Додаємо таймаут на рівні API SDK
                    request_options={"timeout": 15}
                )

                if model_name != MODELS[0]:
                    print(
                        f"[Gemini] Відновлено роботу на резервній моделі: {model_name}")
                return response

            except Exception as e:
                error_str = str(e).lower()
                last_error = error_str

                if '429' in error_str or 'resource_exhausted' in error_str:
                    print(
                        f"[Gemini] {model_name} — Rate limit. Спроба {attempt + 1}/{max_retries}.")
                    continue  # Пробуємо наступну модель відразу
                elif 'not found' in error_str or '404' in error_str:
                    continue  # Ця модель не існує, йдемо до наступної
                else:
                    # Для інших помилок (таймаут, інше) логуємо і пробуємо знову
                    print(
                        f"[Gemini] Помилка на моделі {model_name}. Причина: {error_str}")
                    continue

        # Якщо ми перебрали всі моделі і все ще помилка
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff (1s, 2s, 4s...)
            print(
                f"[Gemini] Всі моделі у ліміті або зависли. Чекаємо {wait_time} секунд...")
            time.sleep(wait_time)

    raise Exception(
        f"Google Gemini API недоступне після {max_retries} спроб. Остання помилка: {last_error}")
