"""
Тести для AI-агентів фінансового планування.
Використовуємо unittest.mock для ізоляції від реального Gemini API.
"""
import math
import pytest
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────
# Допоміжна фабрика транзакцій
# ─────────────────────────────────────────────

def make_tx(amount: float, tx_type: str, date: str = "2026-03-15T10:00:00", desc: str = "Test") -> dict:
    return {"amount": amount, "type": tx_type, "transaction_date": date, "description": desc}


def mock_gemini_response(text: str = "OK") -> MagicMock:
    resp = MagicMock()
    resp.text = text
    candidate = MagicMock()
    part = MagicMock()
    part.function_call = None
    part.text = text
    candidate.content.parts = [part]
    resp.candidates = [candidate]
    return resp


# ─────────────────────────────────────────────
# ForecastAgent — чиста математика
# ─────────────────────────────────────────────

class TestForecastMath:
    """Перевіряємо чисту математику без Gemini"""

    def setup_method(self):
        from finance.services.agents.forecast import ForecastAgent
        self.agent = ForecastAgent

    def test_linear_regression_flat(self):
        slope, intercept = self.agent._linear_regression([100, 100, 100, 100])
        assert slope == pytest.approx(0, abs=1e-6)
        assert intercept == pytest.approx(100, abs=1e-6)

    def test_linear_regression_growing(self):
        # y = 10*x + 5 → slope=10, intercept=5
        y = [5 + 10 * x for x in range(6)]
        slope, intercept = self.agent._linear_regression(y)
        assert slope == pytest.approx(10, abs=1e-4)
        assert intercept == pytest.approx(5, abs=1e-4)

    def test_linear_regression_single_point(self):
        slope, intercept = self.agent._linear_regression([200])
        assert slope == 0
        assert intercept == 200

    def test_rmse_perfect_prediction(self):
        actual = [100, 200, 300]
        predicted = [100, 200, 300]
        assert self.agent._rmse(actual, predicted) == 0.0

    def test_rmse_known_value(self):
        actual = [10, 20, 30]
        predicted = [12, 18, 33]
        # errors: 2, 2, 3 → mse = (4+4+9)/3 = 17/3 → rmse ≈ 2.38
        expected = round(math.sqrt((4 + 4 + 9) / 3), 2)
        assert self.agent._rmse(actual, predicted) == expected

    def test_mae_known_value(self):
        actual = [10, 20, 30]
        predicted = [12, 18, 33]
        # |2|+|2|+|3| = 7 / 3 ≈ 2.33
        assert self.agent._mae(actual, predicted) == pytest.approx(7 / 3, abs=0.01)

    def test_r_squared_perfect(self):
        data = [10, 20, 30, 40, 50]
        slope, intercept = self.agent._linear_regression(data)
        predicted = self.agent._predict_series(slope, intercept, list(range(len(data))))
        assert self.agent._r_squared(data, predicted) == pytest.approx(1.0, abs=1e-4)

    def test_r_squared_bad_model(self):
        actual = [10, 20, 30, 40]
        predicted = [40, 30, 20, 10]  # протилежна лінія
        r2 = self.agent._r_squared(actual, predicted)
        assert r2 < 0  # негативний R² означає модель гірша за середнє

    def test_evaluate_model_returns_metrics(self):
        series = [100, 110, 120, 130, 140, 150, 160, 170]
        metrics = self.agent._evaluate_model(series)
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert metrics['rmse'] is not None

    def test_evaluate_model_too_short(self):
        metrics = self.agent._evaluate_model([100, 200])
        assert metrics['rmse'] is None

    @patch("finance.services.agents.forecast.generate_with_retry")
    def test_forecast_returns_required_keys(self, mock_gen):
        mock_gen.return_value = mock_gemini_response("Прогноз виконано")
        transactions = [
            make_tx(500, "expense", "2026-03-01T10:00:00"),
            make_tx(400, "expense", "2026-03-08T10:00:00"),
            make_tx(600, "expense", "2026-03-15T10:00:00"),
            make_tx(550, "expense", "2026-03-22T10:00:00"),
            make_tx(2000, "income", "2026-03-05T10:00:00"),
            make_tx(2100, "income", "2026-03-12T10:00:00"),
            make_tx(2050, "income", "2026-03-19T10:00:00"),
            make_tx(2200, "income", "2026-03-26T10:00:00"),
        ]
        from finance.services.agents.forecast import ForecastAgent
        result = ForecastAgent.forecast(transactions, days=30)

        assert 'forecast' in result
        assert 'data' in result
        data = result['data']
        assert 'forecast_expense' in data
        assert 'forecast_income' in data
        assert 'forecast_balance' in data
        assert 'accuracy' in data
        assert 'expenses' in data['accuracy']
        assert 'income' in data['accuracy']

    @patch("finance.services.agents.forecast.generate_with_retry")
    def test_forecast_no_transactions(self, mock_gen):
        from finance.services.agents.forecast import ForecastAgent
        result = ForecastAgent.forecast([], days=30)
        assert 'forecast' in result
        mock_gen.assert_not_called()

    @patch("finance.services.agents.forecast.generate_with_retry")
    def test_forecast_expense_not_negative(self, mock_gen):
        mock_gen.return_value = mock_gemini_response()
        # Різко падаючий ряд — прогноз не має стати від'ємним
        transactions = [make_tx(1000 - i * 100, "expense", f"2026-03-{i+1:02d}T10:00:00") for i in range(8)]
        from finance.services.agents.forecast import ForecastAgent
        result = ForecastAgent.forecast(transactions, days=30)
        assert result['data']['forecast_expense'] >= 0


# ─────────────────────────────────────────────
# AnomalyDetectorAgent — статистика MAD
# ─────────────────────────────────────────────

class TestAnomalyDetector:

    def setup_method(self):
        from finance.services.agents.anomaly_detector import AnomalyDetectorAgent
        self.agent = AnomalyDetectorAgent

    def test_median_odd(self):
        assert self.agent._median([3, 1, 2]) == 2

    def test_median_even(self):
        assert self.agent._median([1, 2, 3, 4]) == 2.5

    def test_detect_too_few_transactions(self):
        txs = [make_tx(100, "expense") for _ in range(4)]
        result = self.agent.detect(txs)
        assert result['anomaly_count'] == 0

    @patch("finance.services.agents.anomaly_detector.generate_with_retry")
    def test_detect_finds_anomaly(self, mock_gen):
        mock_gen.return_value = mock_gemini_response("Знайдено аномалію")
        # 9 звичайних витрат + 1 гігантська
        transactions = [make_tx(100, "expense", f"2026-03-{i+1:02d}T10:00:00") for i in range(9)]
        transactions.append(make_tx(10000, "expense", "2026-03-10T10:00:00", "Велика покупка"))
        result = self.agent.detect(transactions)
        assert result['anomaly_count'] >= 1
        assert len(result['anomalous_transactions']) >= 1
        assert result['anomalous_transactions'][0]['amount'] == 10000

    @patch("finance.services.agents.anomaly_detector.generate_with_retry")
    def test_detect_no_anomalies_uniform(self, mock_gen):
        mock_gen.return_value = mock_gemini_response("Аномалій немає")
        transactions = [make_tx(200, "expense", f"2026-03-{i+1:02d}T10:00:00") for i in range(10)]
        result = self.agent.detect(transactions)
        assert result['anomaly_count'] == 0

    @patch("finance.services.agents.anomaly_detector.generate_with_retry")
    def test_detect_ignores_income(self, mock_gen):
        mock_gen.return_value = mock_gemini_response()
        transactions = [make_tx(100, "expense", f"2026-03-{i+1:02d}T10:00:00") for i in range(8)]
        transactions += [make_tx(50000, "income", "2026-03-09T10:00:00")]
        result = self.agent.detect(transactions)
        # Дохід 50000 не має впливати на threshold витрат
        assert result['anomaly_count'] == 0


# ─────────────────────────────────────────────
# InvestmentAdvisorAgent — логіка портфелю
# ─────────────────────────────────────────────

class TestInvestmentAdvisor:

    def setup_method(self):
        from finance.services.agents.investment_advisor import InvestmentAdvisorAgent
        self.agent = InvestmentAdvisorAgent

    def test_risk_profile_aggressive(self):
        # Висока норма заощадження + великий баланс
        risk = self.agent._calculate_risk_profile(balance=50000, income=20000, expenses=10000)
        assert risk['level'] == 'aggressive'
        assert risk['savings_rate'] == pytest.approx(50.0)

    def test_risk_profile_conservative(self):
        # Майже немає заощаджень, малий баланс
        risk = self.agent._calculate_risk_profile(balance=500, income=10000, expenses=9800)
        assert risk['level'] == 'conservative'

    def test_risk_profile_moderate(self):
        risk = self.agent._calculate_risk_profile(balance=15000, income=10000, expenses=7000)
        assert risk['level'] in ('moderate', 'aggressive')

    def test_risk_emergency_fund_covered(self):
        # 3 місяці витрат = 30000, баланс 35000 → покрито
        risk = self.agent._calculate_risk_profile(balance=35000, income=15000, expenses=10000)
        assert risk['emergency_fund_needed'] == pytest.approx(30000)
        assert risk['emergency_fund_covered'] is True

    def test_build_portfolio_deficit(self):
        risk = self.agent._calculate_risk_profile(1000, 5000, 6000)
        portfolio = self.agent._build_portfolio(savings=-1000, balance=1000, risk=risk)
        assert portfolio['total_to_invest'] == 0

    def test_build_portfolio_has_allocations(self):
        risk = self.agent._calculate_risk_profile(50000, 20000, 8000)
        portfolio = self.agent._build_portfolio(savings=12000, balance=50000, risk=risk)
        assert len(portfolio['allocations']) > 0
        assert portfolio['total_to_invest'] > 0

    def test_build_portfolio_amounts_sum_correctly(self):
        risk = self.agent._calculate_risk_profile(50000, 20000, 8000)
        savings = 12000.0
        portfolio = self.agent._build_portfolio(savings=savings, balance=50000, risk=risk)
        total_allocated = sum(a['amount'] for a in portfolio['allocations'])
        assert total_allocated == pytest.approx(savings, abs=1.0)

    @patch("finance.services.agents.investment_advisor.generate_with_retry")
    def test_advise_returns_required_keys(self, mock_gen):
        mock_gen.return_value = mock_gemini_response("Інвестиційна порада")
        from finance.services.agents.investment_advisor import InvestmentAdvisorAgent
        result = InvestmentAdvisorAgent.advise({'balance': 30000, 'income': 15000, 'expenses': 8000})
        assert 'advice' in result
        assert 'risk_profile' in result
        assert 'portfolio' in result
        assert result['risk_profile']['level'] in ('conservative', 'moderate', 'aggressive')

    @patch("finance.services.agents.investment_advisor.generate_with_retry")
    def test_advise_with_exchange_data(self, mock_gen):
        mock_gen.return_value = mock_gemini_response()
        from finance.services.agents.investment_advisor import InvestmentAdvisorAgent
        result = InvestmentAdvisorAgent.advise(
            {'balance': 20000, 'income': 12000, 'expenses': 8000},
            exchange_data={'BTC': 0.01, 'ETH': 0.5}
        )
        assert 'advice' in result


# ─────────────────────────────────────────────
# FinancialAnalystAgent — smoke tests
# ─────────────────────────────────────────────

class TestFinancialAnalyst:

    @patch("finance.services.agents.financial_analyst.generate_with_retry")
    def test_analyze_no_transactions(self, mock_gen):
        from finance.services.agents.financial_analyst import FinancialAnalystAgent
        result = FinancialAnalystAgent.analyze([])
        assert 'analysis' in result
        mock_gen.assert_not_called()

    @patch("finance.services.agents.financial_analyst.generate_with_retry")
    def test_analyze_with_transactions(self, mock_gen):
        mock_gen.return_value = mock_gemini_response("Аналіз виконано")
        transactions = [
            make_tx(3000, "income"),
            make_tx(500, "expense"),
            make_tx(200, "expense"),
        ]
        from finance.services.agents.financial_analyst import FinancialAnalystAgent
        result = FinancialAnalystAgent.analyze(transactions)
        assert result['data']['income'] == 3000
        assert result['data']['expenses'] == 700
        assert result['data']['balance'] == 2300

    @patch("finance.services.agents.financial_analyst.generate_with_retry")
    def test_analyze_with_question(self, mock_gen):
        mock_gen.return_value = mock_gemini_response("Відповідь на питання")
        from finance.services.agents.financial_analyst import FinancialAnalystAgent
        result = FinancialAnalystAgent.analyze(
            [make_tx(1000, "income"), make_tx(300, "expense")],
            user_question="Скільки я заощадив?"
        )
        assert result['analysis'] == "Відповідь на питання"
