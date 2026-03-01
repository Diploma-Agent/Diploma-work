from google import genai
import os


# Ініціалізація Gemini через новий пакет
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY', 'AIzaSyB3k-WUJ-av7C4zWZqaS1ZRf6oE5qc-mZU'))
MODEL = 'gemini-2.5-flash'


from .agents import (
    FinancialAnalystAgent,
    InvestmentAdvisorAgent,
    ForecastAgent,
    AnomalyDetectorAgent,
    ChatAgent
)

__all__ = [
    'FinancialAnalystAgent',
    'InvestmentAdvisorAgent',
    'ForecastAgent',
    'AnomalyDetectorAgent',
    'ChatAgent'
]
