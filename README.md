# Diploma Work - Financial Management System

Цей проект є комплексною системою управління особистими фінансами, розробленою для агрегації даних з різних фінансових джерел. Система дозволяє користувачам підключати свої банківські рахунки та акаунти криптовалютних бірж, автоматично синхронізувати транзакції та переглядати детальну аналітику своїх активів.

## Основні можливості

*   **Мульти-акаунтинг**: Підтримка декількох джерел даних для одного користувача.
*   **Банківські інтеграції**:
    *   **Monobank**: Автоматична синхронізація балансів та транзакцій.
    *   **PUMB (ПУМБ)**: Інтеграція з рахунками ПУМБ.
*   **Криптовалютні інтеграції**:
    *   **Binance**: Відстеження спотових балансів.
    *   **Bybit**: Інтеграція з акаунтом Bybit.
    *   **OKX**: Підтримка біржі OKX.
*   **Безпека даних**: Всі чутливі дані (API ключі, токени доступу) зберігаються в базі даних у зашифрованому вигляді (AES шифрування).
*   **Аналітика**: Візуалізація доходів та витрат, розподіл активів по категоріях та валютах.
*   **Управління транзакціями**: Перегляд історії операцій, категоризація витрат.

## Технологічний стек

### Backend
*   **Python 3.8+**
*   **Django 4.1+**: Основний веб-фреймворк.
*   **Django Rest Framework (DRF)**: Для побудови REST API.
*   **MongoDB**: Основна база даних (використовується через `djongo` для ORM сумісності).
*   **Celery & Redis**: Для обробки фонових задач (синхронізація транзакцій, оновлення курсів валют).
*   **JWT (JSON Web Tokens)**: Для безпечної аутентифікації користувачів.
*   **Cryptography**: Бібліотека для шифрування API ключів та токенів.

### Frontend
*   **React 19**: Бібліотека для побудови інтерфейсу користувача.
*   **Vite**: Інструмент для збірки та запуску dev-сервера.
*   **React Router**: Маршрутизація на стороні клієнта.
*   **Axios**: HTTP клієнт для взаємодії з Backend API.
*   **CSS Modules**: Стилізація компонентів.

## Структура проекту

Проект розділений на дві основні частини: `backend` та `frontend`.

### Backend (`/backend`)

*   **`config/`**: Налаштування проекту Django (settings.py, urls.py, celery.py).
*   **`authentication/`**: Додаток для реєстрації та авторизації користувачів.
*   **`finance/`**: Основний додаток з бізнес-логікою.
    *   **`models.py`**: Опис моделей даних (`UserProfile`, `BankConnection`, `CryptoExchange`, `TransactionCategory`). Містить кастомне поле `EncryptedField` для шифрування.
    *   **`services/`**: Модулі інтеграції із зовнішніми API (`monobank.py`, `binance.py`, `pumb.py` тощо).
    *   **`tasks.py`**: Задачі Celery для фонової синхронізації.
    *   **`views.py`**: API Endpoints для фронтенду.
*   **`docs/`**: Документація по інтеграціях (наприклад, PUMB flow).

### Frontend (`/frontend`)

*   **`src/`**: Вихідний код React додатку.
    *   **`api/`**: Сервіси для запитів до бекенду (`authService.js`, `financeService.js`).
    *   **`components/`**: Перевикористовувані компоненти (наприклад, `Navbar`, таби профілю).
    *   **`templates/`**: Сторінки додатку:
        *   `Dashboard.jsx`: Головна панель з оглядом активів.
        *   `Analytics.jsx`: Сторінка з графіками та статистикою.
        *   `Transactions.jsx`: Історія транзакцій.
        *   `Profile.jsx`: Налаштування профілю та підключення банків/бірж.
        *   `Login.jsx` / `Register.jsx`: Сторінки авторизації.
    *   **`styles/`**: CSS файли стилів для сторінок.
    *   **`utils/`**: Допоміжні функції.

## Попередні вимоги

Перед запуском переконайтеся, що у вас встановлено:
- [Python](https://www.python.org/) (3.8+)
- [Node.js](https://nodejs.org/) (16+)
- [MongoDB](https://www.mongodb.com/) (локально або Atlas)
- [Redis](https://redis.io/) (для роботи Celery)

## Встановлення та налаштування

### 1. Клонування репозиторію

```bash
git clone <repository-url>
cd Diploma-work
```

### 2. Налаштування Backend

Перейдіть у папку backend:
```bash
cd backend
```

Створіть віртуальне середовище та активуйте його:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

Встановіть залежності:
```bash
pip install -r requirements.txt
```

Створіть файл `.env` у папці `backend` та додайте необхідні змінні середовища:
```env
SECRET_KEY=your_secret_key_here
DEBUG=True
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=diploma_db
# Інші змінні за необхідності
```

Виконайте міграції бази даних:
```bash
python manage.py migrate
```

### 3. Налаштування Frontend

Перейдіть у папку frontend:
```bash
cd ../frontend
```

Встановіть залежності:
```bash
npm install
```

## Запуск проекту

У кореневій папці проекту є скрипти для швидкого запуску обох частин (backend та frontend).

### Windows (PowerShell)
```powershell
.\start.ps1
```

### Linux/macOS (Bash)
```bash
chmod +x start.sh
./start.sh
```

### Ручний запуск

Якщо ви хочете запустити сервіси окремо:

**Backend:**
```bash
cd backend
# Активуйте venv
python manage.py runserver
```
*Для запуску Celery (в окремому терміналі):*
```bash
celery -A config worker -l info
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Додаток буде доступний за адресою: `http://localhost:5173` (або інший порт, вказаний Vite).
API буде доступне за адресою: `http://localhost:8000`.
