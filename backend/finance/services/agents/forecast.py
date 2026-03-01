from .base import client, MODEL, generate_with_retry
from datetime import datetime


class ForecastAgent:
    """Агент-прогнозист фінансових показників"""
    
    SYSTEM_PROMPT = """
    Ти - фінансовий прогнозист.
    Роби точні прогнози на основі historical даних.
    Відповідай українською мовою з конкретними числами. Максимум 250 слів.
    """
    
    @staticmethod
    def forecast(transactions: list, days: int = 30) -> dict:
        if not transactions:
            return {'forecast': 'Недостатньо даних для прогнозу.', 'agent': 'Прогнозист'}
        
        weekly_expenses = {}
        weekly_income = {}
        
        for t in transactions:
            try:
                date_str = t['transaction_date']
                # Сумісність з Django timezone-aware форматом
                if '+' in date_str:
                    date_str = date_str.split('+')[0]
                elif date_str.endswith('Z'):
                    date_str = date_str[:-1]
                date = datetime.fromisoformat(date_str)
                week = date.strftime('%Y-W%W')
                if t['type'] == 'expense':
                    weekly_expenses[week] = weekly_expenses.get(week, 0) + t['amount']
                elif t['type'] == 'income':
                    weekly_income[week] = weekly_income.get(week, 0) + t['amount']
            except Exception:
                continue
        
        avg_weekly_expense = sum(weekly_expenses.values()) / len(weekly_expenses) if weekly_expenses else 0
        avg_weekly_income = sum(weekly_income.values()) / len(weekly_income) if weekly_income else 0
        forecast_expense = avg_weekly_expense * (days / 7)
        forecast_income = avg_weekly_income * (days / 7)
        
        prompt = f"""
        {ForecastAgent.SYSTEM_PROMPT}
        - Середні тижневі витрати: {avg_weekly_expense:.2f} UAH
        - Середні тижневі доходи: {avg_weekly_income:.2f} UAH
        - Прогноз витрат на {days} днів: {forecast_expense:.2f} UAH
        - Прогноз доходів на {days} днів: {forecast_income:.2f} UAH
        Зроби детальний прогноз та поради щодо оптимізації витрат.
        """
        
        response = generate_with_retry(contents=prompt)
        return {
            'forecast': response.text,
            'agent': 'Прогнозист',
            'data': {
                'forecast_expense': round(forecast_expense, 2),
                'forecast_income': round(forecast_income, 2),
                'forecast_balance': round(forecast_income - forecast_expense, 2),
                'period_days': days
            }
        }
