from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # Отримуємо стандартну відповідь помилки
    response = exception_handler(exc, context)

    # Якщо є відповідь з помилкою (наприклад, 400), друкуємо її в консоль
    if response is not None:
        print(f"\n>>> ERROR DETAILS: {response.data}\n")

    return response
