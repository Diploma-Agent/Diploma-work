from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Спочатку викликаємо стандартний обробник DRF
    response = exception_handler(exc, context)

    # Якщо DRF не зміг обробити помилку самостійно (наприклад, це звичайний Exception)
    if response is None:
        logger.error(f"Необроблена помилка: {str(exc)}", exc_info=True)
        
        return Response({
            'error': 'Внутрішня помилка сервера. Наші спеціалісти вже працюють над цим.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Форматуємо стандартні помилки DRF у наш єдиний формат { "error": "..." }
    if isinstance(response.data, dict):
        if 'detail' in response.data:
            response.data = {'error': response.data['detail']}
            
    return response