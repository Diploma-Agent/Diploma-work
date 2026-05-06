from .base import MODEL, generate_with_retry
from datetime import datetime
import math


class ForecastAgent:
    """
    Агент-прогнозист фінансових показників.

    Алгоритм:
      - Витрати: тижнева агрегація (витрати рівномірні протягом місяця)
      - Доходи: автоматичний вибір агрегації —
          * якщо > 45% тижнів мають дохід → тижнева (доходи рівномірні)
          * інакше → місячна (зарплата 1–2 рази на місяць)
        Це усуває проблему «нульових тижнів», яка занижує R² при місячній зарплаті.
      - Модель: МНК лінійна регресія (slope/intercept)
      - Оцінка: train/test split 75/25, метрики RMSE, MAE, R²
    """

    SYSTEM_PROMPT = """
    Ти — особистий фінансовий радник. Говори напряму, як людина людині, без заголовків і форматування.
    Суцільний текст кількома короткими абзацами. Без markdown, без зірочок, без решіток, без списків.
    Скажи головне: як рухаються витрати та доходи, що буде через місяць, і одну конкретну пораду що змінити.
    Тон — спокійний, чіткий, як порада від знайомого фінансиста. Максимум 120 слів. Тільки українська.
    """

    WEEKS_PER_MONTH = 4.345  # середня кількість тижнів у місяці

    # ──────────────────────────────────────────────────────────────
    # Математика
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _linear_regression(y_values: list) -> tuple:
        """МНК: повертає (slope, intercept)."""
        n = len(y_values)
        if n < 2:
            return 0, sum(y_values) / max(n, 1)
        x_values = list(range(n))
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_xx = sum(x * x for x in x_values)
        denom = (n * sum_xx) - (sum_x ** 2)
        slope = ((n * sum_xy) - (sum_x * sum_y)) / denom if denom else 0
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept

    @staticmethod
    def _predict_series(slope: float, intercept: float, x_values: list) -> list:
        return [intercept + slope * x for x in x_values]

    @staticmethod
    def _rmse(actual: list, predicted: list) -> float:
        if not actual or len(actual) != len(predicted):
            return 0.0
        mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual)
        return round(math.sqrt(mse), 2)

    @staticmethod
    def _mae(actual: list, predicted: list) -> float:
        if not actual or len(actual) != len(predicted):
            return 0.0
        return round(sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual), 2)

    @staticmethod
    def _r_squared(actual: list, predicted: list) -> float:
        """R² на тестовій вибірці."""
        if not actual or len(actual) < 2:
            return 0.0
        mean_a = sum(actual) / len(actual)
        ss_tot = sum((a - mean_a) ** 2 for a in actual)
        ss_res = sum((a - p) ** 2 for a, p in zip(actual, predicted))
        return round(1 - ss_res / ss_tot, 4) if ss_tot else 1.0

    @staticmethod
    def _evaluate_model(series: list) -> dict:
        """Train/test split 75/25. Потребує мінімум 4 точки."""
        n = len(series)
        if n < 4:
            return {'rmse': None, 'mae': None, 'r2': None,
                    'test_weeks': 0, 'train_weeks': n}
        split = max(2, int(n * 0.75))
        train, test = series[:split], series[split:]
        slope, intercept = ForecastAgent._linear_regression(train)
        predicted = ForecastAgent._predict_series(slope, intercept, list(range(split, n)))
        return {
            'rmse': ForecastAgent._rmse(test, predicted),
            'mae': ForecastAgent._mae(test, predicted),
            'r2': ForecastAgent._r_squared(test, predicted),
            'test_weeks': len(test),
            'train_weeks': len(train),
        }

    # ──────────────────────────────────────────────────────────────
    # Допоміжні
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        ds = date_str
        if '+' in ds:
            ds = ds.split('+')[0]
        elif ds.endswith('Z'):
            ds = ds[:-1]
        return datetime.fromisoformat(ds)

    @staticmethod
    def _r2_label(r2) -> str:
        """Людиночитана мітка якості моделі."""
        if r2 is None:
            return 'недостатньо даних'
        if r2 >= 0.7:
            return 'висока'
        if r2 >= 0.4:
            return 'задовільна'
        if r2 >= 0.1:
            return 'низька'
        return 'дуже низька'

    # ──────────────────────────────────────────────────────────────
    # Основний метод
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def forecast(transactions: list, days: int = 30) -> dict:
        if not transactions:
            return {'forecast': 'Недостатньо даних для прогнозу.', 'agent': 'Прогнозист'}

        # ── 1. Тижнева агрегація ──────────────────────────────────
        weekly_expenses: dict = {}
        weekly_income_raw: dict = {}  # для перевірки розрідженості
        monthly_income: dict = {}

        for t in transactions:
            try:
                dt = ForecastAgent._parse_date(t['transaction_date'])
                week = dt.strftime('%Y-W%W')
                month = dt.strftime('%Y-%m')
                if t['type'] == 'expense':
                    weekly_expenses[week] = weekly_expenses.get(week, 0) + t['amount']
                elif t['type'] == 'income':
                    weekly_income_raw[week] = weekly_income_raw.get(week, 0) + t['amount']
                    monthly_income[month] = monthly_income.get(month, 0) + t['amount']
            except Exception:
                continue

        sorted_weeks = sorted(set(weekly_expenses.keys()) | set(weekly_income_raw.keys()))
        if not sorted_weeks:
            return {'forecast': 'Недостатньо даних для прогнозу.', 'agent': 'Прогнозист'}

        exp_series = [weekly_expenses.get(w, 0) for w in sorted_weeks]

        # ── 2. Вибір агрегації для доходів ───────────────────────
        # Якщо зарплата 1–2 рази на місяць → більшість тижнів = 0 → тижнева R² буде низькою.
        # Перемикаємось на місячну агрегацію коли < 45% тижнів мають ненульовий дохід.
        income_filled_pct = (
            sum(1 for w in sorted_weeks if weekly_income_raw.get(w, 0) > 0) / len(sorted_weeks)
        )
        use_monthly_income = income_filled_pct < 0.45

        if use_monthly_income and len(monthly_income) >= 2:
            sorted_months = sorted(monthly_income.keys())
            inc_series_base = [monthly_income[m] for m in sorted_months]

            inc_slope_base, inc_intercept_base = ForecastAgent._linear_regression(inc_series_base)
            inc_metrics = ForecastAgent._evaluate_model(inc_series_base)

            # Конвертуємо місячні коефіцієнти у тижневі для єдиної формули прогнозу
            inc_slope = inc_slope_base / ForecastAgent.WEEKS_PER_MONTH
            inc_intercept = inc_intercept_base / ForecastAgent.WEEKS_PER_MONTH
            avg_weekly_income = (
                sum(inc_series_base) / len(inc_series_base) / ForecastAgent.WEEKS_PER_MONTH
            )
            # Тренд у зручних одиницях для відображення
            inc_trend_display = inc_slope_base   # грн/міс
            inc_trend_unit = 'month'
            inc_agg_label = 'місячна'
        else:
            # Тижнева агрегація (доходи рівномірні або даних недостатньо для місячної)
            inc_series_base = [weekly_income_raw.get(w, 0) for w in sorted_weeks]
            inc_slope, inc_intercept = ForecastAgent._linear_regression(inc_series_base)
            inc_metrics = ForecastAgent._evaluate_model(inc_series_base)
            avg_weekly_income = sum(inc_series_base) / len(inc_series_base) if inc_series_base else 0
            inc_trend_display = inc_slope  # грн/тиж
            inc_trend_unit = 'week'
            inc_agg_label = 'тижнева'

        # ── 3. Тренд і прогноз витрат ────────────────────────────
        exp_slope, exp_intercept = ForecastAgent._linear_regression(exp_series)
        exp_metrics = ForecastAgent._evaluate_model(exp_series)
        avg_weekly_expense = sum(exp_series) / len(exp_series) if exp_series else 0

        # ── 4. Прогноз на days днів ──────────────────────────────
        weeks_to_forecast = days / 7
        future_week_idx = len(sorted_weeks) + (weeks_to_forecast / 2)

        pred_exp = max(
            exp_intercept + exp_slope * future_week_idx,
            avg_weekly_expense * 0.5
        )
        pred_inc = max(
            inc_intercept + inc_slope * future_week_idx,
            avg_weekly_income * 0.5
        )

        forecast_expense = round(pred_exp * weeks_to_forecast, 2)
        forecast_income = round(pred_inc * weeks_to_forecast, 2)
        forecast_balance = round(forecast_income - forecast_expense, 2)

        # ── 5. Рядки для промпту ─────────────────────────────────
        exp_unit = 'грн/тиж'
        exp_trend_str = (
            f"зростають на {abs(exp_slope):.0f} {exp_unit}" if exp_slope > 0
            else f"спадають на {abs(exp_slope):.0f} {exp_unit}"
        )
        inc_unit = 'грн/міс' if inc_trend_unit == 'month' else 'грн/тиж'
        inc_trend_str = (
            f"зростають на {abs(inc_trend_display):.0f} {inc_unit}" if inc_trend_display > 0
            else f"спадають на {abs(inc_trend_display):.0f} {inc_unit}"
        )

        def fmt_metrics(m: dict) -> str:
            if m['rmse'] is None:
                return 'недостатньо даних для оцінки'
            label = ForecastAgent._r2_label(m['r2'])
            return (
                f"MAE={m['mae']:.2f} грн, RMSE={m['rmse']:.2f} грн, "
                f"R²={m['r2']:.3f} ({label}), "
                f"навч.: {m['train_weeks']} / тест: {m['test_weeks']} пер."
            )

        data_weeks = len(sorted_weeks)
        data_months = len(monthly_income)

        prompt = f"""
        {ForecastAgent.SYSTEM_PROMPT}

        Дані для аналізу ({data_weeks} тижнів / {data_months} місяців з БД):
        Витрати {exp_trend_str}, в середньому {avg_weekly_expense:.0f} грн/тиж.
        Доходи {inc_trend_str}, в середньому {avg_weekly_income:.0f} грн/тиж (агрегація: {inc_agg_label}).
        Прогноз на {days} днів: витрати {forecast_expense:.0f} UAH, надходження {forecast_income:.0f} UAH, баланс {forecast_balance:.0f} UAH.
        Точність моделі: витрати — {fmt_metrics(exp_metrics)}; доходи — {fmt_metrics(inc_metrics)}.
        """

        response = generate_with_retry(contents=prompt)

        return {
            'forecast': response.text,
            'agent': 'Прогнозист',
            'data': {
                'forecast_expense': forecast_expense,
                'forecast_income': forecast_income,
                'forecast_balance': forecast_balance,
                'period_days': days,
                'exp_trend': round(exp_slope, 2),
                'inc_trend': round(inc_trend_display, 2),
                'inc_trend_unit': inc_trend_unit,   # 'week' або 'month'
                'data_weeks': data_weeks,
                'data_months': data_months,
                'inc_aggregation': inc_agg_label,
                'accuracy': {
                    'expenses': exp_metrics,
                    'income': inc_metrics,
                },
            },
        }
