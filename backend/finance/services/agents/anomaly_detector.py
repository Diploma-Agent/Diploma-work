from .base import client, MODEL, generate_with_retry


class AnomalyDetectorAgent:
    """Агент-детектор аномальних витрат"""
    
    SYSTEM_PROMPT = """
    Ти - детектор фінансових аномалій.
    Знаходь незвичні транзакції та відхилення від норми.
    Відповідай українською мовою. Максимум 300 слів.
    """
    
    @staticmethod
    def detect(transactions: list) -> dict:
        if len(transactions) < 5:
            return {
                'anomalies': 'Недостатньо транзакцій (потрібно мінімум 5).',
                'agent': 'Детектор Аномалій',
                'anomaly_count': 0
            }
        
        expenses = [t for t in transactions if t['type'] == 'expense']
        if not expenses:
            return {'anomalies': 'Немає витрат для аналізу.', 'agent': 'Детектор Аномалій', 'anomaly_count': 0}
        
        amounts = [t['amount'] for t in expenses]
        avg_amount = sum(amounts) / len(amounts)
        std_dev = (sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
        
        # Якщо std_dev == 0 - всі суми однакові, аномалій немає
        if std_dev == 0:
            return {
                'anomalies': 'Всі транзакції мають однакову суму — аномалій не виявлено.',
                'agent': 'Детектор Аномалій',
                'anomaly_count': 0
            }
        
        threshold = avg_amount + 2 * std_dev
        anomalous = [t for t in expenses if t['amount'] > threshold]
        
        anomaly_text = "\n".join([
            f"- {t.get('description', 'Невідомо')[:40]}: {t['amount']:.2f} UAH ({t.get('transaction_date', '')[:10]})"
            for t in anomalous[:5]
        ]) or "Аномалій не знайдено"
        
        prompt = f"""
        {AnomalyDetectorAgent.SYSTEM_PROMPT}
        - Середня сума: {avg_amount:.2f} UAH
        - Стандартне відхилення: {std_dev:.2f} UAH
        - Поріг аномалії: {threshold:.2f} UAH
        - Знайдено аномалій: {len(anomalous)}
        Аномальні транзакції: {anomaly_text}
        """
        
        response = generate_with_retry(contents=prompt)
        return {
            'anomalies': response.text,
            'agent': 'Детектор Аномалій',
            'anomaly_count': len(anomalous),
            'anomalous_transactions': [
                {'description': t.get('description', ''), 'amount': t['amount'], 'date': t.get('transaction_date', '')[:10]}
                for t in anomalous[:5]
            ]
        }
