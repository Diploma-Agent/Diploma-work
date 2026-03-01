from google import genai
from google.genai import types
import os
import re
import time
from django.conf import settings

api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY не встановлено в .env файлі")

client = genai.Client(api_key=api_key)

# Моделі у порядку пріоритету — автоматичний fallback
MODELS = [
    'gemini-2.5-flash-preview-05-20',
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
]
MODEL = MODELS[0]


def generate_with_retry(contents, config=None, max_retries=1):
    """Виклик Gemini API з retry логікою та автоматичним fallback між моделями"""
    last_error = None

    for model in MODELS:
        for attempt in range(max_retries):
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
                    # Не чекаємо — одразу переходимо до наступної моделі
                    print(f"[Gemini] {model} — ліміт, переходимо далі...")
                    break

                elif 'not found' in error_str.lower() or '404' in error_str or 'invalid' in error_str.lower():
                    print(f"[Gemini] {model} не знайдена, пробуємо наступну...")
                    break

                else:
                    raise e

    raise Exception(f"Всі Gemini моделі недоступні. Спробуйте пізніше.")
