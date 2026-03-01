from .base import generate_with_retry
from google.genai import types


class ChatAgent:
    """Загальний чат-агент для фінансових питань"""
    
    SYSTEM_PROMPT = """
    Ти - персональний фінансовий асистент FinanceApp на базі Gemini 2.5.
    Відповідай природно на питання користувача, пам'ятай контекст всієї розмови.
    Якщо питання про фінанси, бюджет, витрати, інвестиції — допомагай з цим детально.
    Якщо є дані користувача в контексті — використовуй їх ЛИШЕ коли питання стосується його фінансів.
    Якщо питання просте (привітання) — відповідай коротко і природно, БЕЗ згадки фінансових даних.
    Якщо питання не стосується фінансів — ввічливо поясни свою спеціалізацію.
    Відповідай українською мовою, простим текстом БЕЗ markdown (без **, ##, *, bullets).
    Пам'ятай всі попередні повідомлення в розмові та враховуй їх при відповіді.
    """

    FINANCIAL_DATA_KEYWORDS = [
        'витрат', 'доход', 'баланс', 'заробив', 'витратив', 'залишок',
        'скільки', 'мої гроші', 'мій рахунок', 'аналіз', 'звіт', 'гроші'
    ]

    # Який агент відповідає залежно від теми
    AGENT_KEYWORDS = {
        'Фінансовий Аналітик 📊': ['аналіз', 'транзакц', 'витрат', 'доход', 'звіт', 'статистик'],
        'Інвестиційний Радник 💹': ['інвест', 'вкладен', 'портфел', 'акц', 'крипт', 'біткоїн', 'купит'],
        'Прогнозист 🔮': ['прогноз', 'майбутн', 'наступн', 'плану', 'передбач'],
        'Детектор Аномалій 🔍': ['аномал', 'незвичн', 'підозр', 'великі витрати'],
    }

    @staticmethod
    def _needs_context(message: str) -> bool:
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in ChatAgent.FINANCIAL_DATA_KEYWORDS)

    @staticmethod
    def _get_agent_name(message: str) -> str:
        msg_lower = message.lower()
        for agent_name, keywords in ChatAgent.AGENT_KEYWORDS.items():
            if any(kw in msg_lower for kw in keywords):
                return agent_name
        return 'Фінансовий Асистент 🤖'

    @staticmethod
    def chat(message: str, context: dict = None, history: list = None) -> dict:
        context_text = ""
        if context and ChatAgent._needs_context(message):
            context_text = f"""
            [Фінансові дані користувача:
            - Баланс: {context.get('balance', 'невідомо')} UAH
            - Доходи за місяць: {context.get('income', 'невідомо')} UAH
            - Витрати за місяць: {context.get('expenses', 'невідомо')} UAH]
            """

        # Будуємо історію у форматі Gemini — максимум 20 останніх повідомлень
        contents = []
        if history:
            recent_history = history[-20:]  # обмежуємо пам'ять
            for msg in recent_history:
                contents.append({
                    'role': msg['role'],
                    'parts': [{'text': msg['text']}]
                })

        current = f"{context_text}\n{message}" if context_text else message
        contents.append({
            'role': 'user',
            'parts': [{'text': current}]
        })

        response = generate_with_retry(
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=ChatAgent.SYSTEM_PROMPT
            )
        )

        agent_name = ChatAgent._get_agent_name(message)

        return {
            'response': response.text,
            'agent': agent_name
        }
