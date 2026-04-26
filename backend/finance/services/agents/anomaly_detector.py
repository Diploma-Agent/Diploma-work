from .base import MODEL, generate_with_retry


class AnomalyDetectorAgent:
    """Агент-детектор аномальних витрат за допомогою робастної статистики (MAD)"""

    SYSTEM_PROMPT = """
    Ти - детектор фінансових аномалій. Ми вже проаналізували дані за допомогою 
    медіанного абсолютного відхилення (MAD - Median Absolute Deviation) і знайшли підозрілі транзакції.
    Проаналізуй їх: чи це просто великі покупки (техніка, меблі), чи можливо шахрайство, чи підписки.
    Дай короткі рекомендації.
    Відповідай українською мовою. Максимум 300 слів.
    """

    @staticmethod
    def _median(lst):
        sorted_lst = sorted(lst)
        n = len(lst)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_lst[mid - 1] + sorted_lst[mid]) / 2.0
        return sorted_lst[mid]

    @staticmethod
    def detect(transactions: list) -> dict:
        if len(transactions) < 5:
            return {
                'anomalies': 'Недостатньо транзакцій (потрібно мінімум 5) для статистичного аналізу.',
                'agent': 'Детектор Аномалій',
                'anomaly_count': 0
            }

        expenses = [t for t in transactions if t['type'] == 'expense']
        if not expenses:
            return {'anomalies': 'Немає витрат для аналізу.', 'agent': 'Детектор Аномалій', 'anomaly_count': 0}

        amounts = [t['amount'] for t in expenses]

        # Використовуємо MAD замість StdDev (Mean + 2*Std), оскільки фінанси мають "важкий хвіст"
        median_amount = AnomalyDetectorAgent._median(amounts)
        mad = AnomalyDetectorAgent._median(
            [abs(x - median_amount) for x in amounts])

        # Якщо MAD = 0, усі витрати майже однакові. Додаємо мінімальний поріг.
        if mad == 0:
            mad = 1.0

        # Формула аномалії: значення > Медіана + 3 * MAD (або хоча б в 3 рази більше медіани)
        threshold = max(median_amount + 3 * mad, median_amount * 2.5)

        anomalous = [t for t in expenses if t['amount'] > threshold]

        anomaly_text = "\n".join([
            f"- {t.get('description', 'Невідомо')[:40]}: {t['amount']:.2f} UAH ({t.get('transaction_date', '')[:10]})"
            for t in anomalous[:5]
        ]) or "Математичних аномалій не знайдено (усі витрати в межах вашої типової поведінки)."

        prompt = f"""
        {AnomalyDetectorAgent.SYSTEM_PROMPT}
        - Типова (медіанна) витрата: {median_amount:.2f} UAH
        - Обчислене відхилення (MAD): {mad:.2f} UAH
        - Поріг математичної аномалії: {threshold:.2f} UAH
        - Знайдено аномалій: {len(anomalous)}
        
        Ось знайдений список аномальних транзакцій: 
        {anomaly_text}
        
        Поясни, чому це може бути аномалією, і чи варто користувачу хвилюватися.
        """

        response = generate_with_retry(contents=prompt)
        return {
            'anomalies': response.text,
            'agent': 'Детектор Аномалій',
            'anomaly_count': len(anomalous),
            'anomalous_transactions': [
                {'description': t.get('description', ''), 'amount': t['amount'], 'date': t.get(
                    'transaction_date', '')[:10]}
                for t in anomalous[:5]
            ]
        }
