from .base import client, MODEL, generate_with_retry


class InvestmentAdvisorAgent:
    """Агент-інвестиційний радник"""
    
    SYSTEM_PROMPT = """
    Ти - досвідчений інвестиційний радник з фокусом на криптовалюти та традиційні фінанси.
    Аналізуй фінансовий стан та надавай конкретні інвестиційні рекомендації.
    Завжди вказуй ризики. Відповідай українською мовою. Максимум 300 слів.
    """
    
    @staticmethod
    def advise(bank_data: dict, exchange_data: dict = None) -> dict:
        balance = bank_data.get('balance', 0)
        income = bank_data.get('income', 0)
        expenses = bank_data.get('expenses', 0)
        savings = income - expenses
        
        prompt = f"""
        {InvestmentAdvisorAgent.SYSTEM_PROMPT}
        Фінансовий стан:
        - Баланс: {balance:.2f} UAH
        - Доходи: {income:.2f} UAH
        - Витрати: {expenses:.2f} UAH
        - Профіцит: {savings:.2f} UAH
        {f"Портфель на біржі: {exchange_data}" if exchange_data else ""}
        
        Надай рекомендації: скільки інвестувати, куди, стратегія, ризики.
        """
        
        response = generate_with_retry(contents=prompt)
        safe_investment = max(0, savings * 0.3) if savings > 0 else 0
        
        return {
            'advice': response.text,
            'agent': 'Інвестиційний Радник',
            'recommended_investment': round(safe_investment, 2),
            'risk_level': 'medium' if balance > 10000 else 'low'
        }
