from .base import MODEL, generate_with_retry
from datetime import datetime
import math


class ForecastAgent:
    """Агент-прогнозист фінансових показників з використанням Лінійної Регресії та метриками точності"""

    SYSTEM_PROMPT = """
    Ти - фінансовий аналітик і прогнозист.
    Ми проаналізували історію транзакцій (тренди) і зробили розрахунки математичною регресією (тренд і прогноз).
    Все, що тобі потрібно — проаналізувати ці цифри і дати користувачу професійний коментар та поради щодо оптимізації.
    Обов'язково поясни користувачу його 'тренд' — тобто чи ростуть його витрати щотижня, чи падають.
    Відповідай українською мовою з конкретними числами. Максимум 300 слів.
    """

    @staticmethod
    def _linear_regression(y_values: list) -> tuple:
        """Проста лінійна регресія (МНК) для знаходження тренду. Повертає (slope, intercept)."""
        n = len(y_values)
        if n < 2:
            return 0, sum(y_values) / max(n, 1)

        x_values = list(range(n))
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_xx = sum(x * x for x in x_values)

        numerator = (n * sum_xy) - (sum_x * sum_y)
        denominator = (n * sum_xx) - (sum_x ** 2)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept

    @staticmethod
    def _predict_series(slope: float, intercept: float, x_values: list) -> list:
        """Повертає список прогнозних значень для заданих індексів x."""
        return [intercept + slope * x for x in x_values]

    @staticmethod
    def _rmse(actual: list, predicted: list) -> float:
        """Root Mean Squared Error"""
        if not actual or len(actual) != len(predicted):
            return 0.0
        mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual)
        return round(math.sqrt(mse), 2)

    @staticmethod
    def _mae(actual: list, predicted: list) -> float:
        """Mean Absolute Error"""
        if not actual or len(actual) != len(predicted):
            return 0.0
        return round(sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual), 2)

    @staticmethod
    def _r_squared(actual: list, predicted: list) -> float:
        """Коефіцієнт детермінації R² — показує якість апроксимації (0..1)"""
        if not actual or len(actual) < 2:
            return 0.0
        mean_actual = sum(actual) / len(actual)
        ss_tot = sum((a - mean_actual) ** 2 for a in actual)
        ss_res = sum((a - p) ** 2 for a, p in zip(actual, predicted))
        if ss_tot == 0:
            return 1.0
        return round(1 - ss_res / ss_tot, 4)

    @staticmethod
    def _evaluate_model(series: list) -> dict:
        """
        Оцінює точність моделі методом train/test split (75%/25%).
        Повертає словник з RMSE, MAE, R².
        """
        n = len(series)
        if n < 4:
            return {'rmse': None, 'mae': None, 'r2': None, 'test_weeks': 0}

        split = max(2, int(n * 0.75))
        train = series[:split]
        test = series[split:]

        slope, intercept = ForecastAgent._linear_regression(train)
        test_x = list(range(split, n))
        predicted = ForecastAgent._predict_series(slope, intercept, test_x)

        return {
            'rmse': ForecastAgent._rmse(test, predicted),
            'mae': ForecastAgent._mae(test, predicted),
            'r2': ForecastAgent._r_squared(test, predicted),
            'test_weeks': len(test),
            'train_weeks': len(train),
        }

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
                    weekly_expenses[week] = weekly_expenses.get(week, 0) + t['amount']
                elif t['type'] == 'income':
                    weekly_income[week] = weekly_income.get(week, 0) + t['amount']
            except Exception:
                continue

        sorted_weeks = sorted(set(weekly_expenses.keys()) | set(weekly_income.keys()))
        exp_series = [weekly_expenses.get(w, 0) for w in sorted_weeks]
        inc_series = [weekly_income.get(w, 0) for w in sorted_weeks]

        # Тренди (навчання на всіх даних)
        exp_slope, exp_intercept = ForecastAgent._linear_regression(exp_series)
        inc_slope, inc_intercept = ForecastAgent._linear_regression(inc_series)

        avg_weekly_expense = sum(exp_series) / len(exp_series) if exp_series else 0
        avg_weekly_income = sum(inc_series) / len(inc_series) if inc_series else 0

        # Прогноз на X днів
        weeks_to_forecast = days / 7
        future_week_idx = len(sorted_weeks) + (weeks_to_forecast / 2)

        predicted_weekly_exp = exp_intercept + exp_slope * future_week_idx
        predicted_weekly_inc = inc_intercept + inc_slope * future_week_idx

        predicted_weekly_exp = max(predicted_weekly_exp, avg_weekly_expense * 0.5)
        predicted_weekly_inc = max(predicted_weekly_inc, avg_weekly_income * 0.5)

        forecast_expense = predicted_weekly_exp * weeks_to_forecast
        forecast_income = predicted_weekly_inc * weeks_to_forecast

        # Метрики точності (train/test split)
        exp_metrics = ForecastAgent._evaluate_model(exp_series)
        inc_metrics = ForecastAgent._evaluate_model(inc_series)

        exp_trend_str = (
            f"зростають на {abs(exp_slope):.0f} грн/тиж" if exp_slope > 0
            else f"спадають на {abs(exp_slope):.0f} грн/тиж"
        )
        inc_trend_str = (
            f"зростають на {abs(inc_slope):.0f} грн/тиж" if inc_slope > 0
            else f"спадають на {abs(inc_slope):.0f} грн/тиж"
        )

        def fmt_metrics(m: dict) -> str:
            if m['rmse'] is None:
                return "недостатньо даних для оцінки"
            return (
                f"MAE={m['mae']:.2f} грн, RMSE={m['rmse']:.2f} грн, R²={m['r2']:.3f} "
                f"(навчання: {m['train_weeks']} тиж, тест: {m['test_weeks']} тиж)"
            )

        prompt = f"""
        {ForecastAgent.SYSTEM_PROMPT}

        --- ДАНІ МАШИННОГО АНАЛІЗУ (Лінійна регресія + екстраполяція) ---
        Тренд витрат: {exp_trend_str}
        Тренд доходів: {inc_trend_str}
        Середні витрати (факт): {avg_weekly_expense:.2f} грн/тиж
        Середні доходи (факт): {avg_weekly_income:.2f} грн/тиж

        --- МЕТРИКИ ТОЧНОСТІ МОДЕЛІ (train/test split 75/25) ---
        Витрати: {fmt_metrics(exp_metrics)}
        Доходи:  {fmt_metrics(inc_metrics)}

        --- ПРОГНОЗ НА {days} ДНІВ ---
        Очікувані витрати: {forecast_expense:.2f} UAH
        Очікувані надходження: {forecast_income:.2f} UAH
        Прогнозований баланс: {forecast_income - forecast_expense:.2f} UAH

        Проаналізуй прогнозований баланс. Порадь як згладити негативний тренд витрат (якщо такий є).
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
                'inc_trend': round(inc_slope, 2),
                'accuracy': {
                    'expenses': exp_metrics,
                    'income': inc_metrics,
                }
            }
        }
