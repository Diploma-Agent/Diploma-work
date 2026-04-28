from .base import MODEL, generate_with_retry


class InvestmentAdvisorAgent:
    """Агент-інвестиційний радник з диверсифікацією портфелю"""

    SYSTEM_PROMPT = """
    Ти - досвідчений інвестиційний радник з фокусом на криптовалюти та традиційні фінанси.
    Тобі передають готовий розрахований план розподілу коштів — поясни його користувачу простою мовою.
    Обов'язково: поясни логіку кожного активу, потенційний прибуток та ризики кожної частини.
    Відповідай українською мовою. Максимум 350 слів.
    """

    # Мінімальна кількість місяців витрат у резервному фонді
    EMERGENCY_MONTHS = 3

    @staticmethod
    def _calculate_risk_profile(balance: float, income: float, expenses: float) -> dict:
        """Визначає профіль ризику на основі декількох факторів"""
        savings = income - expenses
        savings_rate = (savings / income * 100) if income > 0 else 0
        monthly_expenses = expenses
        emergency_fund_needed = monthly_expenses * InvestmentAdvisorAgent.EMERGENCY_MONTHS

        # Скоринг ризику: 0-100
        score = 0

        # 1. Норма заощадження (до 40 балів)
        if savings_rate >= 30:
            score += 40
        elif savings_rate >= 20:
            score += 30
        elif savings_rate >= 10:
            score += 20
        elif savings_rate > 0:
            score += 10

        # 2. Розмір резервного фонду (до 30 балів)
        if balance >= emergency_fund_needed * 2:
            score += 30
        elif balance >= emergency_fund_needed:
            score += 20
        elif balance >= emergency_fund_needed * 0.5:
            score += 10

        # 3. Стабільність: доходи покривають витрати (до 30 балів)
        if income > 0 and expenses > 0:
            ratio = income / expenses
            if ratio >= 1.5:
                score += 30
            elif ratio >= 1.2:
                score += 20
            elif ratio >= 1.0:
                score += 10

        if score >= 70:
            level = 'aggressive'
            label = 'Агресивний'
        elif score >= 40:
            level = 'moderate'
            label = 'Помірний'
        else:
            level = 'conservative'
            label = 'Консервативний'

        return {
            'level': level,
            'label': label,
            'score': score,
            'savings_rate': round(savings_rate, 1),
            'emergency_fund_needed': round(emergency_fund_needed, 2),
            'emergency_fund_covered': balance >= emergency_fund_needed,
        }

    @staticmethod
    def _build_portfolio(savings: float, balance: float, risk: dict) -> dict:
        """Будує диверсифікований портфель відповідно до профілю ризику"""
        if savings <= 0:
            return {'total_to_invest': 0, 'allocations': [], 'note': 'Дефіцит бюджету — інвестиції недоступні'}

        # Спочатку — поповнення резервного фонду
        emergency_gap = max(0, risk['emergency_fund_needed'] - balance)
        reserve_fill = min(savings * 0.3, emergency_gap)  # не більше 30% заощаджень на резерв
        available = savings - reserve_fill

        if available <= 0:
            return {
                'total_to_invest': round(reserve_fill, 2),
                'allocations': [{'name': 'Резервний фонд', 'amount': round(reserve_fill, 2), 'percent': 100}],
                'note': 'Пріоритет — формування резервного фонду'
            }

        # Розподіл за профілем ризику
        if risk['level'] == 'conservative':
            # 60% депозит / ОВДП, 30% золото/USD, 10% крипто (stable)
            alloc_pct = [('Депозит / ОВДП (гривня)', 60), ('Золото або USD депозит', 30), ('Crypto Stablecoin (USDT)', 10)]
        elif risk['level'] == 'moderate':
            # 40% депозит, 30% ETF/акції, 20% крипто, 10% gold
            alloc_pct = [('Депозит / ОВДП', 40), ('ETF / Індексні фонди (S&P 500)', 30), ('Криптовалюта (BTC/ETH)', 20), ('Золото', 10)]
        else:  # aggressive
            # 20% депозит, 30% акції, 35% крипто, 15% DeFi/альткоїни
            alloc_pct = [('Депозит (ліквідний буфер)', 20), ('Акції / ETF', 30), ('Криптовалюта (BTC/ETH)', 35), ('Альткоїни / DeFi', 15)]

        allocations = []
        if reserve_fill > 0:
            allocations.append({'name': 'Резервний фонд (пріоритет)', 'amount': round(reserve_fill, 2), 'percent': None})

        for name, pct in alloc_pct:
            amount = available * pct / 100
            allocations.append({'name': name, 'amount': round(amount, 2), 'percent': pct})

        return {
            'total_to_invest': round(savings, 2),
            'allocations': allocations,
        }

    @staticmethod
    def advise(bank_data: dict, exchange_data: dict = None) -> dict:
        balance = bank_data.get('balance', 0)
        income = bank_data.get('income', 0)
        expenses = bank_data.get('expenses', 0)
        savings = income - expenses

        risk = InvestmentAdvisorAgent._calculate_risk_profile(balance, income, expenses)
        portfolio = InvestmentAdvisorAgent._build_portfolio(savings, balance, risk)

        alloc_text = "\n".join(
            f"  - {a['name']}: {a['amount']:.2f} UAH" + (f" ({a['percent']}%)" if a.get('percent') else "")
            for a in portfolio.get('allocations', [])
        )

        prompt = f"""
        {InvestmentAdvisorAgent.SYSTEM_PROMPT}

        --- ФІНАНСОВИЙ СТАН КОРИСТУВАЧА ---
        Баланс: {balance:.2f} UAH
        Доходи за місяць: {income:.2f} UAH
        Витрати за місяць: {expenses:.2f} UAH
        Заощадження (профіцит): {savings:.2f} UAH
        Норма заощадження: {risk['savings_rate']}%
        {f"Портфель на біржі: {exchange_data}" if exchange_data else ""}

        --- ПРОФІЛЬ РИЗИКУ ---
        Рівень: {risk['label']} (скор: {risk['score']}/100)
        Резервний фонд (потрібно): {risk['emergency_fund_needed']:.2f} UAH
        Резервний фонд сформовано: {'Так' if risk['emergency_fund_covered'] else 'Ні — потрібно поповнити'}

        --- РЕКОМЕНДОВАНИЙ РОЗПОДІЛ КОШТІВ ---
        Загалом до інвестування: {portfolio['total_to_invest']:.2f} UAH
{alloc_text}

        Поясни користувачу цей план, логіку вибору активів та ризики кожного.
        """

        response = generate_with_retry(contents=prompt)

        return {
            'advice': response.text,
            'agent': 'Інвестиційний Радник',
            'risk_profile': risk,
            'portfolio': portfolio,
        }
