# 💳 BanFin — AI-помічник для розумного фінансового планування

> Веб-застосунок для автоматичного збору, аналізу та AI-прогнозування особистих фінансів з підтримкою банківських рахунків та криптовалютних бірж.

---

## 👤 Автор

- **ПІБ**: Гаврилюк Микола
- **Група**: ФЕІ-44
- **Керівник**: Гура Володимир, кандидат технічних наук, асистент
- **Тема дипломної роботи**: Розробка AI-помічника для розумного фінансового планування

---

## 📌 Загальна інформація

- **Тип проєкту**: Full-stack веб-застосунок (SPA + REST API)
- **Мови програмування**: Python, JavaScript
- **Frontend**: React 18 + Vite
- **Backend**: Django 4.1 + Django REST Framework
- **База даних**: MongoDB (через djongo + PyMongo)
- **AI-модель**: Google Gemini (google-generativeai)
- **Черга задач**: Celery + Redis
- **Деплой**: Render.com (backend + frontend)

---

## 🧠 Опис функціоналу

### 🔐 Авторизація
- Реєстрація та вхід з JWT-токенами (djangorestframework-simplejwt)
- Збереження профілю користувача

### 🏦 Підключення банків
- Інтеграція з **Monobank API** (токен доступу) — автоматичний імпорт транзакцій
- Інтеграція з **ПУМБ** — через OAuth2
- Підтримка кількох банківських підключень одночасно
- Фонова синхронізація транзакцій через Celery

### 💹 Підключення криптобірж
- Інтеграція з **Binance**, **Bybit**, **OKX** через API-ключі
- Отримання балансів гаманців та відкритих ордерів (Spot / Futures)
- Синхронізація крипто-транзакцій

### 📊 Аналітика
- Дашборд із загальним балансом, доходами та витратами за місяць
- Фільтрація по окремих банківських рахунках
- Графік доходів і витрат по днях
- Donut-діаграма розподілу витрат по категоріях
- Вибір довільного місяця/року для аналізу

### 🤖 AI-агенти (на базі Google Gemini)

| Агент | Призначення |
|---|---|
| **ChatAgent** | Загальний фінансовий чат-асистент з Function Calling (AI Routing) |
| **FinancialAnalystAgent** | Аналіз доходів, витрат та транзакцій за будь-який період |
| **ForecastAgent** | Прогноз доходів і витрат на 30 днів методом лінійної регресії (МНК) |
| **AnomalyDetectorAgent** | Виявлення підозрілих та аномальних транзакцій |
| **InvestmentAdvisorAgent** | Поради щодо інвестицій на основі поточного балансу |

**Особливості AI-чату:**
- Персистентна історія повідомлень у MongoDB
- Function Calling (AI Router): автоматичне делегування між агентами
- Доступ до реальних даних бірж (портфель у USDT по кожній монеті)
- Підтримка запитів за будь-який часовий діапазон

### 💬 Транзакції
- Перегляд та фільтрація транзакцій (по джерелу, типу, даті, акаунту)
- Ручне додавання транзакцій
- Підтримка типів: дохід, витрата, переказ

---

## 🧱 Структура проєкту

```
Diploma-work/
├── backend/
│   ├── authentication/          # Реєстрація, вхід, профіль
│   │   ├── models.py            # UserProfile
│   │   ├── views.py             # RegisterView, LoginView, GetMeView
│   │   └── serializers.py
│   ├── finance/
│   │   ├── models.py            # BankConnection, CryptoExchange, Transaction, ChatMessage
│   │   ├── views.py             # Всі API-ендпоінти
│   │   ├── tasks.py             # Celery-задачі синхронізації
│   │   └── services/
│   │       ├── monobank.py      # Monobank API інтеграція
│   │       ├── pumb.py          # ПУМБ OAuth2
│   │       ├── binance.py       # Binance API
│   │       ├── bybit.py         # Bybit API
│   │       ├── okx.py           # OKX API
│   │       └── agents/
│   │           ├── base.py               # Базовий виклик Gemini з retry
│   │           ├── chat.py               # ChatAgent (Function Calling)
│   │           ├── financial_analyst.py  # FinancialAnalystAgent
│   │           ├── forecast.py           # ForecastAgent (МНК регресія)
│   │           ├── anomaly_detector.py   # AnomalyDetectorAgent
│   │           └── investment_advisor.py # InvestmentAdvisorAgent
│   ├── config/
│   │   ├── settings.py          # Налаштування Django
│   │   └── celery.py            # Celery конфігурація
│   └── requirements.txt
└── frontend/
    └── src/
        ├── templates/
        │   ├── Dashboard.jsx    # Головна сторінка з балансом і транзакціями
        │   ├── Analytics.jsx    # Аналітика банку та біржі
        │   ├── Transactions.jsx # Список транзакцій з фільтрами
        │   └── Profile.jsx      # Управління підключеннями
        ├── components/
        │   ├── ChatComponent.jsx       # AI чат-вікно
        │   ├── Navbar.jsx              # Навігація
        │   └── profile/
        │       ├── BanksTab.jsx        # Підключення банків
        │       └── TokensTab.jsx       # Підключення бірж
        ├── context/
        │   ├── FinanceContext.jsx      # Контекст + хук useFinance
        │   └── FinanceProvider.jsx     # Кеш-провайдер (TTL 5 хв)
        └── api/
            ├── financeService.js       # Всі запити до finance API
            └── authService.js          # Запити авторизації
```

---

## ▶️ Як запустити проєкт локально

### 1. Потрібні інструменти

- Python 3.11+
- Node.js 18+ та npm
- MongoDB (локально або Atlas)
- Redis (для Celery)

### 2. Клонування репозиторію

```bash
git clone https://github.com/Diploma-Agent/Diploma-work.git
cd Diploma-work
```

### 3. Налаштування Backend

```bash
cd backend
pip install -r requirements.txt
```

Створіть файл `.env` у папці `backend/`:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
MONGODB_DATABASE=banfin
GEMINI_API_KEY=your-gemini-api-key
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:5173
ENCRYPTION_KEY=your-fernet-encryption-key
```

Запуск сервера:

```bash
python manage.py migrate
python manage.py runserver
```

Запуск Celery (в окремому терміналі):

```bash
celery -A config worker --loglevel=info
```

### 4. Налаштування Frontend

```bash
cd frontend
npm install --legacy-peer-deps
```

Створіть файл `.env` у папці `frontend/`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Запуск:

```bash
npm run dev
```

Відкрийте [http://localhost:5173](http://localhost:5173)

---

## 🔌 Основні API-ендпоінти

### 🔐 Авторизація

| Метод | URL | Опис |
|---|---|---|
| POST | `/api/auth/register/` | Реєстрація |
| POST | `/api/auth/login/` | Вхід (отримання JWT) |
| GET | `/api/auth/me/` | Профіль поточного користувача |

### 🏦 Банки

| Метод | URL | Опис |
|---|---|---|
| GET | `/api/finance/banks/` | Список підключених банків |
| POST | `/api/finance/banks/add/` | Додати банк |
| DELETE | `/api/finance/banks/{id}/delete/` | Видалити банк |
| GET | `/api/finance/analytics/bank/?connection_id=` | Баланс конкретного банку |

### 💹 Біржі

| Метод | URL | Опис |
|---|---|---|
| GET | `/api/finance/exchanges/` | Список підключених бірж |
| POST | `/api/finance/exchanges/add/` | Додати біржу |
| DELETE | `/api/finance/exchanges/{id}/delete/` | Видалити біржу |
| GET | `/api/finance/exchanges/balance/?exchange=binance` | Баланс біржі |
| GET | `/api/finance/exchanges/orders/?exchange=bybit` | Відкриті ордери |

### 📋 Транзакції

| Метод | URL | Опис |
|---|---|---|
| GET | `/api/finance/transactions/?days=30` | Список транзакцій |
| POST | `/api/finance/transactions/sync/` | Синхронізація з банком/біржею |

### 🤖 AI

| Метод | URL | Опис |
|---|---|---|
| POST | `/api/finance/ai/chat/` | Чат з AI-асистентом |
| GET | `/api/finance/ai/chat/history/` | Історія чату |
| DELETE | `/api/finance/ai/chat/history/` | Очистити історію |
| POST | `/api/finance/ai/analyst/` | Фінансовий аналіз |
| GET | `/api/finance/ai/forecast/?days=30&connection_id=` | Прогноз на N днів |
| GET | `/api/finance/ai/anomaly/` | Виявлення аномалій |
| GET | `/api/finance/ai/investment/` | Інвестиційні поради |

---

## 🖱️ Інструкція для користувача

1. **Реєстрація / Вхід** — створіть акаунт або увійдіть у систему

2. **Підключення банку** (Профіль → Банки):
   - Отримайте токен у застосунку Monobank: Налаштування → Особистий токен
   - Вставте токен і вкажіть назву підключення
   - Транзакції за останні 2 місяці синхронізуються автоматично у фоні

3. **Підключення біржі** (Профіль → Токени бірж):
   - Створіть API-ключ у Binance / Bybit / OKX
   - Вставте API Key та Secret (для OKX — ще й Passphrase)

4. **Дашборд** — загальний огляд балансу, доходів і витрат, фільтрація по банку

5. **Аналітика**:
   - Вибір банку (чіп) та місяця → оновлення всіх віджетів
   - AI-прогноз на 30 днів методом лінійної регресії (МНК)
   - Розподіл витрат по категоріях (donut-діаграма)
   - Баланс та ордери криптобіржі

6. **AI-чат** — запитайте про ваші фінанси природною мовою:
   - *"Скільки я витратив цього місяця?"*
   - *"Проаналізуй мої витрати за березень"*
   - *"Яка ціна Bitcoin зараз?"*
   - *"Скільки монет у мене на Binance?"*

---

## 🧪 Відомі проблеми та рішення

| Проблема | Рішення |
|---|---|
| `npm install` падає з помилкою peer deps | `npm install --legacy-peer-deps` |
| Monobank повертає 429 Too Many Requests | Токен має ліміт 1 запит/60 сек — це нормально, дані кешуються в Redis |
| Celery не запускається на Windows | `celery -A config worker --pool=solo --loglevel=info` |
| `No module named 'whitenoise'` | `pip install -r requirements.txt` |
| CORS помилка при локальному запуску | Перевірте `CORS_ALLOWED_ORIGINS` у `.env` backend |

---

## 🧾 Використані технології та джерела

**Backend:**
- [Django](https://docs.djangoproject.com/) — основний веб-фреймворк
- [Django REST Framework](https://www.django-rest-framework.org/) — побудова REST API
- [djongo + PyMongo](https://www.djongomapper.com/) — ORM-адаптер для MongoDB
- [Celery](https://docs.celeryq.dev/) — фонові задачі та планувальник синхронізації
- [Google Generative AI (Gemini)](https://ai.google.dev/) — AI-агенти
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/) — JWT авторизація
- [drf-yasg](https://drf-yasg.readthedocs.io/) — Swagger документація API

**Frontend:**
- [React 18](https://react.dev/) — UI-бібліотека
- [Vite](https://vitejs.dev/) — збірка та dev-сервер
- [Recharts](https://recharts.org/) — інтерактивні графіки
- [React Router v6](https://reactrouter.com/) — клієнтська маршрутизація

**Зовнішні API:**
- [Monobank API](https://api.monobank.ua/) — банківські транзакції та баланс
- [Binance API](https://binance-docs.github.io/apidocs/) — крипто-баланси
- [Bybit API](https://bybit-exchange.github.io/docs/) — гаманець та ордери
- [OKX API](https://www.okx.com/docs-v5/) — крипто-портфель

---

## 📷 Скриншоти

> Додайте зображення у папку `/screenshots/`

- Дашборд — загальний огляд фінансів
- Аналітика банку — графік, прогноз, розподіл витрат
- Аналітика біржі — баланс монет, ордери
- AI-чат — відповіді на фінансові запити
- Сторінка транзакцій з фільтрами
- Профіль — підключення банків і бірж
