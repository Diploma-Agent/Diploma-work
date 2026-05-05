from .base import generate_with_retry
from .financial_analyst import FinancialAnalystAgent
import requests
import json
import time

def get_crypto_price(symbol: str) -> str:
    """
    Викликай цей інструмент, коли користувач питає поточну ціну (курс, вартість) криптовалюти.
    Аргумент symbol має містити тікер, наприклад: BTC, ETH, SOL, DOGE.
    """
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"Ціна {symbol.upper()} на Binance становить {float(data['price']):.2f} USDT."
        return f"Ціну для {symbol} не знайдено."
    except Exception as e:
        return f"Не вдалося отримати ціну {symbol}."


def analyze_user_finances(days: int = 30, date_from: str = None, date_to: str = None) -> str:
    """
    Викликай цей інструмент, коли користувач просить ГЛИБОКО проаналізувати його фінанси,
    дати фінансову пораду, порівняти доходи з витратами, зробити висновки АБО коли 
    явно просить аналіз за певний період (наприклад, 'за останні 7 днів', 'тільки за січень').
    Якщо користувач просить за абсолютний період (наприклад "за січень", "з 10 по 20 березня"), 
    передавай параметри date_from та date_to у форматі YYYY-MM-DD.
    Якщо вказані date_from та date_to, параметр days ігнорується, інакше використовується days (за замовчуванням 30).
    НЕ використовуй цей інструмент для простих питань типу "Яка поточна ціна біткоїна?".
    """
    if date_from and date_to:
        return f"ACTIVATE_FINANCIAL_ANALYST_DATES_{date_from}_{date_to}"
    return f"ACTIVATE_FINANCIAL_ANALYST_{days}"


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

    Ти допомагаєш виключно з фінансовими питаннями, аналізом бюджету та транзакціями. Якщо користувач ставить запитання, яке не стосується фінансів чи роботи цього додатка, ввічливо відмов та нагадай, що ти фінансовий асистент.
    """

    @staticmethod
    def chat(message: str, context: dict = None, history: list = None, fetch_transactions_cb=None) -> dict:
        context_text = ""
        # Ми додаємо контекст завжди, щоб Gemini знав, які суми є
        if context:
            tx_data = context.get('recent_transactions', [])
            tx_json = json.dumps(
                tx_data, ensure_ascii=False) if tx_data else "[]"

            context_text = (
                f"[Фінансові дані користувача (ЗА ПОТОЧНИЙ МІСЯЦЬ): Баланс {context.get('balance', 0)} UAH, "
                f"Доходи {context.get('income', 0)} UAH, Витрати {context.get('expenses', 0)} UAH]\n"
                f"[Останні транзакції для довідок (ТІЛЬКИ за останні 30 днів): {tx_json}]\n"
                f"УВАГА: Наданий список містить транзакції ВИКЛЮЧНО за останні 30 днів. "
                f"Якщо користувач питає про період, що був РАНІШЕ ніж ці 30 днів (наприклад, 'за січень 2026', 'у грудні'), "
                f"ти ОБОВ'ЯЗКОВО ПОВИНЕН викликати інструмент analyze_user_finances, передавши date_from та date_to у форматі YYYY-MM-DD. "
                f"Шукай відповідь самостійно у наданому вище списку ТІЛЬКИ якщо питання стосується поточного місяця чи останніх 30 днів."
            )

        # Формуємо історію
        contents = []
        if history:
            valid_history = []
            expected_role = 'user'
            
            for msg in history[-10:]:
                role = msg['role']
                if role == expected_role:
                    valid_history.append({
                        'role': role,
                        'parts': [{'text': msg['text']}]
                    })
                    expected_role = 'model' if role == 'user' else 'user'
                elif valid_history:
                    # Якщо ролі дублюються (напр. два 'user' підряд), об'єднуємо їх текст
                    valid_history[-1]['parts'][0]['text'] += f"\n{msg['text']}"

            # Перед новим повідомленням 'user' обов'язково має бути 'model'
            if valid_history and valid_history[-1]['role'] == 'user':
                valid_history.pop()
                
            contents.extend(valid_history)

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
                
                days_raw = args.get('days')
                try:
                    days_requested = int(float(days_raw)) if days_raw is not None else 30
                except (ValueError, TypeError):
                    days_requested = 30

                date_from = args.get('date_from')
                date_to = args.get('date_to')
                print(f"[Gemini args] date_from={date_from}, date_to={date_to}, days={days_raw}")
                
                if date_from == "None" or date_from == "null":
                    date_from = None
                if date_to == "None" or date_to == "null":
                    date_to = None

                transactions = context.get('recent_transactions', [])
                
                if fetch_transactions_cb and (date_from or days_requested != 30):
                    try:
                        # Fetch transactions using callback
                        new_tx = fetch_transactions_cb(days=days_requested, date_from=date_from, date_to=date_to)
                        if new_tx:
                            transactions = [
                                {
                                    'date': t.get('transaction_date', '')[:10],
                                    'type': t.get('type'),
                                    'amount': round(t.get('amount', 0), 2),
                                    'desc': t.get('description', '')[:30]
                                }
                                for t in new_tx
                            ]
                    except Exception as e:
                        print(f"Error fetching specific period transactions: {e}")

                # Формуємо промпт для Аналітика на основі сум та запиту користувача
                analyst_prompt = (
                    f"Запит користувача: '{message}'.\n"
                    f"Його загальні фінансові суми: Баланс {context.get('balance', 0)} UAH.\n"
                    f"Ось список його транзакцій (за {days_requested} днів, {len(transactions)} шт): {transactions}\n\n"
                    f"ВАЖЛИВО: Відповідай МАКСИМАЛЬНО КОРОТКО і СУТО на питання для економії токенів. Нічого зайвого. "
                    f"Якщо він питає конкретну суму — ЗНАЙДИ транзакції, підсумуй їх і дай відповідь одним реченням. "
                    f"Якщо просить аналіз чи пораду — дай дуже стислий висновок без довгих лекцій (максимум 4-5 речень)."
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
            contents.append({
                'role': 'model',
                'parts': [{'text': str(part.function_call)}]
            })
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
