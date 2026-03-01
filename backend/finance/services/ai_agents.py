from google import genai
import os


# Ініціалізація Gemini через новий пакет
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
MODEL = 'gemini-3-flash-preview'


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
