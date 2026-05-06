from .base import generate_with_retry


class FinancialAnalystAgent:
    """
    Агент-аналітик фінансових транзакцій.

    Окрім виклику LLM надає власну аналітику:
      - Розбивка витрат за категоріями (топ-7)
      - Норма заощадження (savings rate)
      - Бюджетний health score (0–100)
    """

    SYSTEM_PROMPT = """
    Ти - досвідчений фінансовий аналітик.
    Аналізуй транзакції користувача та надавай корисні поради українською мовою.
    Будь конкретним, структурованим та практичним.
    Відповідай коротко та по суті (максимум 300 слів).
    Без markdown, без зірочок, без решіток.
    """

    # ──────────────────────────────────────────────────────────────
    # Власна аналітика (не делегується LLM)
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _category_breakdown(transactions: list) -> list:
        """Топ-7 категорій витрат за сумою."""
        totals: dict = {}
        for t in transactions:
            if t.get('type') != 'expense':
                continue
            # Пріоритет: counterparty → перший рядок description → 'Інше'
            cat = (
                t.get('counterparty')
                or (t.get('description', '').split('\n')[0] if t.get('description') else '')
                or 'Інше'
            )
            cat = cat[:30].strip() or 'Інше'
            totals[cat] = totals.get(cat, 0) + t.get('amount', 0)

        return sorted(totals.items(), key=lambda x: x[1], reverse=True)[:7]

    @staticmethod
    def _health_score(income: float, expenses: float, tx_count: int) -> dict:
        """
        Бюджетний health score 0–100.
        Три складові:
          1. Норма заощадження (до 50 балів)
          2. Покриття витрат доходами (до 30 балів)
          3. Достатність даних (до 20 балів)
        """
        score = 0
        savings_rate = round((income - expenses) / income * 100, 1) if income > 0 else 0

        # 1. Норма заощадження
        if savings_rate >= 25:
            score += 50
        elif savings_rate >= 15:
            score += 35
        elif savings_rate >= 5:
            score += 20
        elif savings_rate > 0:
            score += 10

        # 2. Покриття
        if income > 0:
            ratio = income / expenses if expenses > 0 else 2.0
            if ratio >= 1.5:
                score += 30
            elif ratio >= 1.2:
                score += 20
            elif ratio >= 1.0:
                score += 10

        # 3. Достатність даних
        if tx_count >= 30:
            score += 20
        elif tx_count >= 10:
            score += 10

        if score >= 75:
            label = 'Відмінний'
        elif score >= 50:
            label = 'Хороший'
        elif score >= 30:
            label = 'Задовільний'
        else:
            label = 'Потребує уваги'

        return {'score': score, 'label': label, 'savings_rate': savings_rate}

    # ──────────────────────────────────────────────────────────────
    # Публічний метод
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def analyze(transactions: list, user_question: str = None) -> dict:
        if not transactions:
            return {
                'analysis': 'Немає транзакцій для аналізу. Підключіть банківський рахунок.',
                'agent': 'Фінансовий Аналітик',
            }

        income = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income')
        expenses = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')

        categories = FinancialAnalystAgent._category_breakdown(transactions)
        health = FinancialAnalystAgent._health_score(income, expenses, len(transactions))

        top5_text = '\n'.join(
            f'- {cat}: {amt:.2f} UAH ({amt / expenses * 100:.1f}%)' if expenses > 0
            else f'- {cat}: {amt:.2f} UAH'
            for cat, amt in categories[:5]
        )

        cats_text = '\n'.join(
            f'  {i+1}. {cat}: {amt:.2f} UAH'
            for i, (cat, amt) in enumerate(categories)
        )

        prompt = f"""
        {FinancialAnalystAgent.SYSTEM_PROMPT}

        === ФІНАНСОВІ ДАНІ ЗА ПЕРІОД ===
        Доходи: {income:.2f} UAH
        Витрати: {expenses:.2f} UAH
        Баланс (профіцит/дефіцит): {income - expenses:.2f} UAH
        Норма заощадження: {health['savings_rate']}%
        Бюджетний рейтинг: {health['label']} ({health['score']}/100)
        Кількість транзакцій: {len(transactions)}

        === ТОП-5 ВИТРАТ ===
        {top5_text}

        === РОЗБИВКА ЗА КАТЕГОРІЯМИ (топ-7) ===
        {cats_text}

        {"=== ПИТАННЯ КОРИСТУВАЧА ===" if user_question else ""}
        {user_question if user_question else "Зроби загальний аналіз бюджету, вкажи на головні проблеми та одну конкретну пораду."}
        """

        response = generate_with_retry(contents=prompt)

        return {
            'analysis': response.text,
            'agent': 'Фінансовий Аналітик',
            'data': {
                'income': round(income, 2),
                'expenses': round(expenses, 2),
                'balance': round(income - expenses, 2),
                'savings_rate': health['savings_rate'],
                'health_score': health['score'],
                'health_label': health['label'],
                'categories': [
                    {'name': cat, 'amount': round(amt, 2),
                     'percent': round(amt / expenses * 100, 1) if expenses > 0 else 0}
                    for cat, amt in categories
                ],
            },
        }
