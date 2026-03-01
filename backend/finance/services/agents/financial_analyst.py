from .base import generate_with_retry


class FinancialAnalystAgent:
    """Агент-аналітик фінансових транзакцій"""
    
    SYSTEM_PROMPT = """
    Ти - досвідчений фінансовий аналітик. 
    Аналізуй транзакції користувача та надавай корисні поради українською мовою.
    Будь конкретним, структурованим та практичним.
    Відповідай коротко та по суті (максимум 300 слів).
    """
    
    @staticmethod
    def analyze(transactions: list, user_question: str = None) -> dict:
        if not transactions:
            return {
                'analysis': 'Немає транзакцій для аналізу. Підключіть банківський рахунок.',
                'agent': 'Фінансовий Аналітик'
            }
        
        income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        top_expenses = sorted(
            [t for t in transactions if t['type'] == 'expense'],
            key=lambda x: x['amount'], reverse=True
        )[:5]
        
        top_expenses_text = "\n".join([
            f"- {t.get('description', 'Невідомо')[:30]}: {t['amount']:.2f} UAH"
            for t in top_expenses
        ])
        
        prompt = f"""
        {FinancialAnalystAgent.SYSTEM_PROMPT}
        Дані за останній місяць:
        - Загальні доходи: {income:.2f} UAH
        - Загальні витрати: {expenses:.2f} UAH
        - Баланс: {income - expenses:.2f} UAH
        - Кількість транзакцій: {len(transactions)}
        Топ-5 витрат: {top_expenses_text}
        {"Питання: " + user_question if user_question else "Зроби загальний аналіз."}
        """
        
        response = generate_with_retry(contents=prompt)
        return {
            'analysis': response.text,
            'agent': 'Фінансовий Аналітик',
            'data': {'income': income, 'expenses': expenses, 'balance': income - expenses}
        }
