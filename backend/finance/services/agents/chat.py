from .base import generate_with_retry
import requests


def get_crypto_price(symbol: str) -> str:
    """
    Викликай цей інструмент, коли користувач питає поточну ціну (курс, вартість) криптовалюти.
    Аргумент symbol має містити тікер, наприклад: BTC, ETH, SOL, DOGE.
    """
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return f"Ціна {symbol.upper()} на Binance становить {float(data['price']):.2f} USDT."
        return f"Ціну для {symbol} не знайдено."
    except Exception as e:
        return f"Не вдалося отримати ціну {symbol}."


def analyze_user_finances() -> str:
    """
    Викликай цей інструмент, ТІЛЬКИ коли користувач просить ГЛИБОКО проаналізувати його фінанси,
    дати фінансову пораду, порівняти доходи з витратами або зробити висновки.
    НЕ використовуй цей інструмент для простих питань типу "Скільки я витратив?" або "Який мій баланс?" -
    відповідай на такі питання самостійно, використовуючи наданий в системному промпті контекст!
    """
    return "ACTIVATE_FINANCIAL_ANALYST"


class ChatAgent:
    """Загальний чат-агент для фінансових питань (з підтримкою AI Router та Function Calling)"""

    SYSTEM_PROMPT = """
    Ти - професійний фінансовий асистент FinanceApp на базі Gemini (з підтримкою AI Tools).
    У тебе є дві важливі функції (tools):
    1) get_crypto_price - обов'язково викликай, якщо користувач хоче знати курс чи ціну криптовалюти.
    2) analyze_user_finances - обов'язково викликай, якщо користувач питає про аналіз своїх фінансів, витрат і доходів.
    
    ВАЖЛИВО: Відповідай МАКСИМАЛЬНО КОРОТКО і СУТО на поставлене запитання. 
    Не додавай води, вступних слів типу "Звісно, ось відповідь" або непрошених порад. Економ токени.
    Якщо питання просте (привітання), відповідай природно без інструментів, але коротко (1-2 речення).
    Відповідай завжди українською мовою, текстом БЕЗ markdown (тобто без **, ##, *).
    """

    @staticmethod
    def chat(message: str, context: dict = None, history: list = None) -> dict:
        context_text = ""
        # Ми додаємо контекст завжди, щоб Gemini знав, які суми є
        if context:
            import json
            tx_data = context.get('recent_transactions', [])
            tx_json = json.dumps(
                tx_data, ensure_ascii=False) if tx_data else "[]"

            context_text = (
                f"[Фінансові дані користувача (ЗА ПОТОЧНИЙ МІСЯЦЬ): Баланс {context.get('balance', 0)} UAH, "
                f"Доходи {context.get('income', 0)} UAH, Витрати {context.get('expenses', 0)} UAH]\n"
                f"[Останні транзакції для довідок (за 30 днів): {tx_json}]\n"
                f"Якщо користувач питає статистику по певних днях або категоріях/місцях "
                f"(наприклад, 'за цей тиждень', 'сьогодні', 'у Сільпо'), шукай відповідь САМОСТІЙНО "
                f"серед наданого вище списку 'Останні транзакції'."
            )

        # Формуємо історію
        contents = []
        if history:
            # 10 останніх повідомлень для контексту
            recent_history = history[-10:]
            for msg in recent_history:
                contents.append({
                    'role': msg['role'],
                    'parts': [{'text': msg['text']}]
                })

        current = f"{context_text}\nКористувач: {message}" if context_text else message
        contents.append({
            'role': 'user',
            'parts': [{'text': current}]
        })

        # 1. Перший запит до Gemini з передачею інструментів (Tools)
        response = generate_with_retry(
            contents=contents,
            system_instruction=ChatAgent.SYSTEM_PROMPT,
            tools=[get_crypto_price, analyze_user_finances]
        )

        part = response.candidates[0].content.parts[0]

        # 2. Якщо модель вирішила викликати інструмент (відпрацював AI Маршрутизатор або Tools)
        if getattr(part, 'function_call', None) and part.function_call.name:
            fn_name = part.function_call.name
            args = dict(part.function_call.args)

            tool_result = ""
            agent_name = "AI Асистент 🤖"

            if fn_name == 'get_crypto_price':
                # Запит до реального Binance API
                symbol = args.get('symbol', 'BTC')
                tool_result = get_crypto_price(symbol)
                agent_name = "Crypto Інтеграція 💹"

            elif fn_name == 'analyze_user_finances':
                # Делегуємо роботу вузькоспеціалізованому агенту (AI Routing)
                from .financial_analyst import FinancialAnalystAgent

                # Формуємо промпт для Аналітика на основі сум та запиту користувача
                analyst_prompt = (
                    f"Запит користувача: '{message}'.\n"
                    f"Його загальні фінансові суми: Баланс {context.get('balance', 0)} UAH.\n"
                    f"Ось список його останніх транзакцій (до 150 шт): {context.get('recent_transactions', [])}\n\n"
                    f"ВАЖЛИВО: Відповідай МАКСИМАЛЬНО КОРОТКО і СУТО на питання для економії токенів. Нічого зайвого. "
                    f"Якщо він питає конкретну суму — ЗНАЙДИ транзакції, підсумуй їх і дай відповідь одним реченням. "
                    f"Якщо просить аналіз чи пораду — дай дуже стислий висновок без довгих лекцій (максимум 2-3 речення)."
                )
                analyst_response = generate_with_retry(
                    contents=analyst_prompt,
                    system_instruction=FinancialAnalystAgent.SYSTEM_PROMPT
                )
                return {
                    'response': analyst_response.text.replace('*', '').replace('#', ''),
                    'agent': 'Фінансовий Аналітик 📊'
                }

            # Якщо викликався get_crypto_price, треба зробити другий запит, щоб Gemini відформатував відповідь
            # Фіксуємо виклик функції
            contents.append(response.candidates[0].content)
            contents.append({
                'role': 'user',
                'parts': [{'text': f"Результат виклику {fn_name}: {tool_result}. Сформуй природну відповідь користувачу на основі цих даних."}]
            })

            final_response = generate_with_retry(
                contents=contents,
                system_instruction=ChatAgent.SYSTEM_PROMPT
            )

            return {
                'response': final_response.text.replace('*', '').replace('#', ''),
                'agent': agent_name
            }

        # Якщо модель не використовувала інструменти, просто віддаємо текст
        text_response = response.text.replace('*', '').replace('#', '')
        return {
            'response': text_response,
            'agent': 'Фінансовий Асистент 🤖'
        }
