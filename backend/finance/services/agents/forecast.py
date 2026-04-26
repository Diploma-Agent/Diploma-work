from .base import MODEL, generate_with_retry
from datetime import datetime


class ForecastAgent:
    """Агент-прогнозист фінансових показників з використанням Лінійної Регресії для оцінки тренду"""

    SYSTEM_PROMPT = """
    Ти - фінансовий аналітик і прогнозист.
    Ми проаналізували історію транзакцій (тренди) і зробили розрахунки математичною регресією (тренд і прогноз).
    Все, що тобі потрібно — проаналізувати ці цифри і дати користувачу професійний коментар та поради щодо оптимізації.
    Обов'язково поясни користувачу його 'тренд' — тобто чи ростуть його витрати щотижня, чи падають.
    Відповідай українською мовою з конкретними числами. Максимум 300 слів.
    """

    @staticmethod
    def _linear_regression(y_values):
        """Проста лінійна регресія (МНК - Метод Найменших Квадратів) для знаходження тренду"""
        n = len(y_values)
        if n < 2:
            return 0, sum(y_values) / max(n, 1)  # немає тренду

        x_values = list(range(n))
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_xx = sum(x * x for x in x_values)

        # Нахил прямої (slope/trend)
        numerator = (n * sum_xy) - (sum_x * sum_y)
        denominator = (n * sum_xx) - (sum_x ** 2)
        slope = numerator / denominator if denominator != 0 else 0

        # Точка перетину (intercept)
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept

    @staticmethod
    def forecast(transactions: list, days: int = 30) -> dict:
        if not transactions:
            return {'forecast': 'Недостатньо даних для прогнозу.', 'agent': 'Прогнозист'}

        weekly_expenses = {}
        weekly_income = {}

        for t in transactions:
            try:
                date_str = t['transaction_date']
                if '+' in date_str:
                    date_str = date_str.split('+')[0]
                elif date_str.endswith('Z'):
                    date_str = date_str[:-1]
                date = datetime.fromisoformat(date_str)
                week = date.strftime('%Y-W%W')
                if t['type'] == 'expense':
                    weekly_expenses[week] = weekly_expenses.get(
                        week, 0) + t['amount']
                elif t['type'] == 'income':
                    weekly_income[week] = weekly_income.get(
                        week, 0) + t['amount']
            except Exception:
                continue

        # Збираємо у відсортований за тижнями список
        sorted_weeks = sorted(set(weekly_expenses.keys())
                              | set(weekly_income.keys()))
        exp_series = [weekly_expenses.get(w, 0) for w in sorted_weeks]
        inc_series = [weekly_income.get(w, 0) for w in sorted_weeks]

        # Знаходимо тренди (нахил: якщо додатній, то витрати/доходи зростають щотижня)
        exp_slope, exp_intercept = ForecastAgent._linear_regression(exp_series)
        inc_slope, inc_intercept = ForecastAgent._linear_regression(inc_series)

        # Базове середнє
        avg_weekly_expense = sum(exp_series) / \
            len(exp_series) if exp_series else 0
        avg_weekly_income = sum(inc_series) / \
            len(inc_series) if inc_series else 0

        # Обчислюємо прогноз базуючись на тренді, а не просто математичному середньому
        # Формула прогнозу на Х днів (в середньому це Х/7 тижнів):
        weeks_to_forecast = days / 7
        # беремо середину майбутнього періоду
        future_week_idx = len(sorted_weeks) + (weeks_to_forecast / 2)

        predicted_weekly_exp = exp_intercept + exp_slope * future_week_idx
        predicted_weekly_inc = inc_intercept + inc_slope * future_week_idx

        # Уникаємо від'ємних прогнозів
        predicted_weekly_exp = max(
            predicted_weekly_exp, avg_weekly_expense * 0.5)
        predicted_weekly_inc = max(predicted_weekly_inc, avg_weekly_inc * 0.5)

        forecast_expense = predicted_weekly_exp * weeks_to_forecast
        forecast_income = predicted_weekly_inc * weeks_to_forecast

        # Формуємо текст тренду
        exp_trend_str = f"зростають на {abs(exp_slope):.0f} грн/тиж" if exp_slope > 0 else f"спадають на {abs(exp_slope):.0f} грн/тиж"
        inc_trend_str = f"зростають на {abs(inc_slope):.0f} грн/тиж" if inc_slope > 0 else f"спадають на {abs(inc_slope):.0f} грн/тиж"

        prompt = f"""
        {ForecastAgent.SYSTEM_PROMPT}

        --- ДАНІ МАШИННОГО АНАЛІЗУ (Лінійна регресія та екстраполяція) ---
        - Тренд витрат: {exp_trend_str}
        - Тренд доходів: {inc_trend_str}
        - Середні витрати у минулому: {avg_weekly_expense:.2f} грн/тиж
        - Середні доходи у минулому: {avg_weekly_income:.2f} грн/тиж
        
        **Розрахований прогноз (на {days} днів вперед):**
        - Очікувані витрати (до кінця періоду): {forecast_expense:.2f} UAH
        - Очікувані надходження: {forecast_income:.2f} UAH
        
        Проаналізуй прогнозований баланс (різницю). Порадь як згладити негативний тренд витрат (якщо такий є).
        """

        response = generate_with_retry(contents=prompt)
        return {
            'forecast': response.text,
            'agent': 'Прогнозист',
            'data': {
                'forecast_expense': round(forecast_expense, 2),
                'forecast_income': round(forecast_income, 2),
                'forecast_balance': round(forecast_income - forecast_expense, 2),
                'period_days': days,
                'exp_trend': round(exp_slope, 2),
                'inc_trend': round(inc_slope, 2)
            }
        }
