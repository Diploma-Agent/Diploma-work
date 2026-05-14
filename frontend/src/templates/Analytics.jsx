import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Navbar from '../components/Navbar';
import { financeService } from '../api/financeService';
import '../styles/analyticsStyles.css';

function renderForecastText(text) {
    if (!text) return null;
    return text
        .replace(/^#{1,3}\s+(.+)$/gm, '$1')
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/\*(.+?)\*/g, '$1')
        .trim();
}

function Analytics() {
    // --- State для Біржі ---
    const [exchanges, setExchanges] = useState([]);
    const [selectedExchange, setSelectedExchange] = useState('');
    const [balance, setBalance] = useState(null);
    const [spotOrders, setSpotOrders] = useState([]);
    const [futuresOrders, setFuturesOrders] = useState([]);
    const [activeTab, setActiveTab] = useState('spot');

    // --- State для Банку ---
    const [banks, setBanks] = useState([]);
    const [selectedBankId, setSelectedBankId] = useState(null); // null = перший банк після завантаження
    const [bankAnalytics, setBankAnalytics] = useState(null);
    const [bankLoading, setBankLoading] = useState(false);
    const [forecastData, setForecastData] = useState(null);
    const [forecastLoading, setForecastLoading] = useState(false);

    // --- Вибір місяця/року ---
    const now = new Date();
    const [selectedMonth, setSelectedMonth] = useState(now.getMonth());
    const [selectedYear, setSelectedYear]   = useState(now.getFullYear());

    const MONTHS_UK = ['Січень','Лютий','Березень','Квітень','Травень','Червень',
                       'Липень','Серпень','Вересень','Жовтень','Листопад','Грудень'];

    // --- Загальний State ---
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const [hoveredSliceIdx, setHoveredSliceIdx] = useState(null);
    const [hoveredLegendIdx, setHoveredLegendIdx] = useState(null);

    // Завантаження банківських даних для вибраного місяця
    const loadBankDataForPeriod = useCallback(async (month, year, bankIds = []) => {
        const token = localStorage.getItem('token');
        if (!token) return;
        setBankLoading(true);
        try {
            const today = new Date();
            const isCurrentMonth = month === today.getMonth() && year === today.getFullYear();
            // Передаємо ID конкретного банку щоб отримати його баланс
            const connectionId = bankIds.length === 1 ? bankIds[0] : null;

            let bankData;
            if (isCurrentMonth) {
                const [analyticsData, txList] = await Promise.all([
                    financeService.getBankAnalytics(token, connectionId).catch(() => ({ balance: 0 })),
                    financeService.getTransactions(token, 'all', 31, '', '', bankIds, [])
                ]);
                const transactions = Array.isArray(txList) ? txList : (txList?.transactions || []);
                bankData = { balance: analyticsData.balance, transactions };
            } else {
                const mm       = String(month + 1).padStart(2, '0');
                const lastDay  = new Date(year, month + 1, 0).getDate();
                const dateFrom = `${year}-${mm}-01`;
                const dateTo   = `${year}-${mm}-${String(lastDay).padStart(2, '0')}`;

                const [analyticsData, txList] = await Promise.all([
                    financeService.getBankAnalytics(token, connectionId).catch(() => ({ balance: 0 })),
                    financeService.getTransactions(token, 'all', 31, dateFrom, dateTo, bankIds, [])
                ]);

                const transactions = Array.isArray(txList)
                    ? txList
                    : (txList?.transactions || []);

                bankData = { balance: analyticsData.balance, transactions };
            }

            setBankAnalytics(calculateBankAnalytics(bankData, month, year));
        } catch (err) {
            console.error('Помилка завантаження банківської аналітики:', err);
        } finally {
            setBankLoading(false);
        }
    }, []);

    // 1. Початкове завантаження
    useEffect(() => {
        const initData = async () => {
            const token = localStorage.getItem('token');
            if (!token) { navigate('/login'); return; }

            setLoading(true);
            setError('');

            const fetchExchanges = financeService.getExchanges(token)
                .then(list => {
                    setExchanges(list);
                    if (list?.length > 0) setSelectedExchange(list[0].exchange_name);
                })
                .catch(() => setError('Не вдалося завантажити список бірж'));

            const fetchBanks = financeService.getBanks(token)
                .then(list => {
                    const arr = list || [];
                    setBanks(arr);
                    if (arr.length > 0) setSelectedBankId(arr[0].id);
                })
                .catch(() => setBanks([]));

            await Promise.all([fetchExchanges, fetchBanks]);
            setLoading(false);
        };
        initData();
    }, [navigate, loadBankDataForPeriod, selectedMonth, selectedYear]);

    // 2. Перезавантаження банку при зміні місяця/року або вибраного банку
    useEffect(() => {
        if (!loading) loadBankDataForPeriod(selectedMonth, selectedYear, selectedBankId ? [selectedBankId] : []);
    }, [loading, selectedMonth, selectedYear, selectedBankId, loadBankDataForPeriod]);

    // 3. Прогноз — перезавантажуємо при зміні вибраного банку
    useEffect(() => {
        if (!selectedBankId) return;
        const token = localStorage.getItem('token');
        if (!token) return;
        setForecastLoading(true);
        financeService.aiForecast(token, 30, selectedBankId)
            .then(data => setForecastData(data))
            .catch(err => console.error('Помилка AI прогнозу:', err))
            .finally(() => setForecastLoading(false));
    }, [selectedBankId]);

    // 2. Завантаження даних конкретної біржі при зміні вибору
    useEffect(() => {
        if (!selectedExchange) return;

        const fetchExchangeData = async () => {
            const token = localStorage.getItem('token');

            // Одразу скидаємо старі дані, щоб показати прелоадер для компонента
            setBalance(null);
            setSpotOrders([]);
            setFuturesOrders([]);

            // Запускаємо всі запити паралельно для оптимізації швидкості
            const balancePromise = financeService.getExchangeBalance(token, selectedExchange)
                .then(data => setBalance(data?.available === false ? null : data))
                .catch(() => setBalance(null));

            const spotPromise = financeService.getExchangeOrders(token, selectedExchange, 'spot')
                .then(data => setSpotOrders(data?.result?.list || data?.list || []))
                .catch(() => setSpotOrders([]));

            const futuresPromise = financeService.getExchangeOrders(token, selectedExchange, 'linear')
                .then(data => setFuturesOrders(data?.result?.list || data?.list || []))
                .catch(() => setFuturesOrders([]));

            await Promise.all([balancePromise, spotPromise, futuresPromise]);
        };

        fetchExchangeData();
    }, [selectedExchange]);

    // --- Логіка розрахунку банківської аналітики ---
    const calculateBankAnalytics = (bankData, month, year) => {
        if (!bankData || !bankData.transactions) return null;

        const today = new Date();
        const isCurrentMonth = month === today.getMonth() && year === today.getFullYear();

        const startOfPeriod = new Date(year, month, 1);
        const endOfPeriod   = new Date(year, month + 1, 0, 23, 59, 59);

        const monthTransactions = bankData.transactions.filter(t => {
            if (t.type === 'transfer') return false;
            const d = new Date(t.transaction_date);
            return d >= startOfPeriod && d <= endOfPeriod;
        });

        const income   = monthTransactions.filter(t => t.type === 'income')
            .reduce((s, t) => s + parseFloat(t.amount), 0);
        const expenses = monthTransactions.filter(t => t.type === 'expense')
            .reduce((s, t) => s + parseFloat(t.amount), 0);

        // Кількість днів для графіку: для поточного — до сьогодні, для інших — весь місяць
        const daysToShow = isCurrentMonth
            ? today.getDate()
            : new Date(year, month + 1, 0).getDate();

        const chartData = [];
        for (let i = 1; i <= daysToShow; i++) {
            chartData.push({ name: `${i}`, expense: 0, income: 0 });
        }
        monthTransactions.forEach(t => {
            const day = new Date(t.transaction_date).getDate();
            if (day >= 1 && day <= daysToShow && chartData[day - 1]) {
                if (t.type === 'expense') chartData[day - 1].expense += parseFloat(t.amount);
                else if (t.type === 'income') chartData[day - 1].income += parseFloat(t.amount);
            }
        });

        const categoryExpenses = {};
        monthTransactions.filter(t => t.type === 'expense').forEach(t => {
            // counterparty може бути порожнім для старих записів у БД — беремо першу строку description
            const raw = t.counterparty || (t.description ? t.description.split('\n')[0] : '') || 'Інше';
            const cat = raw.trim() || 'Інше';
            categoryExpenses[cat] = (categoryExpenses[cat] || 0) + parseFloat(t.amount);
        });
        const topCategories = Object.entries(categoryExpenses)
            .sort((a, b) => b[1] - a[1]).slice(0, 5)
            .map(([name, amount]) => ({ name, amount }));

        const averageDailyExpenses = expenses / daysToShow;
        const forecastBalance      = bankData.balance - (averageDailyExpenses * 30);
        const safeAmount           = bankData.balance * 0.3;

        return {
            balance: bankData.balance,
            income, expenses,
            netIncome: income - expenses,
            topCategories, chartData,
            averageDailyExpenses: averageDailyExpenses.toFixed(2),
            forecastBalance: forecastBalance.toFixed(2),
            recommendedInvestment: Math.max(0, safeAmount).toFixed(2),
            savingsRate: income > 0 ? ((income - expenses) / income * 100).toFixed(1) : 0
        };
    };

    // --- Рендеринг компонентів біржі ---

    const renderExchangeSelector = () => {
        if (exchanges.length === 0) return null;

        return (
            <div className="exchange-selector">
                <label htmlFor="exchange-select">Оберіть біржу:</label>
                <select
                    id="exchange-select"
                    value={selectedExchange}
                    onChange={(e) => setSelectedExchange(e.target.value)}
                    className="exchange-select-input"
                >
                    {exchanges.map((ex, idx) => (
                        <option key={ex.id || idx} value={ex.exchange_name}>
                            {ex.exchange_name.toUpperCase()}
                        </option>
                    ))}
                </select>
            </div>
        );
    };

    const renderBalance = () => {
        if (!balance) {
            return (
                <div className="analytics-card balance-card">
                    <h3>💰 Баланс ({selectedExchange ? selectedExchange.toUpperCase() : '---'})</h3>
                    <div className="loading-spinner">Завантаження балансу...</div>
                </div>
            );
        }

        // Перевірка структури даних (адаптовано під Bybit API response)
        const accountList = balance?.result?.list || balance?.list;

        if (!accountList?.[0]) {
            return (
                <div className="analytics-card balance-card">
                    <h3>💰 Баланс ({selectedExchange ? selectedExchange.toUpperCase() : '---'})</h3>
                    <div className="no-data">Немає даних про баланс</div>
                </div>
            );
        }

        const account = accountList[0];
        const coins = account.coin || [];

        return (
            <div className="analytics-card balance-card">
                <h3>💰 Баланс ({selectedExchange.toUpperCase()})</h3>
                <div className="total-equity">
                    <span className="label">Загальний капітал:</span>
                    <span className="value">{parseFloat(account.totalEquity).toFixed(2)} USD</span>
                </div>
                <div className="coins-grid">
                    {coins.filter(c => parseFloat(c.walletBalance) > 0).map(coin => (
                        <div key={coin.coin} className="coin-item">
                            <span className="coin-name">{coin.coin}</span>
                            <span className="coin-value">{parseFloat(coin.walletBalance).toFixed(4)}</span>
                            <span className="coin-usd">≈ {parseFloat(coin.usdValue).toFixed(2)} $</span>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const renderOrders = () => {
        const currentOrders = activeTab === 'spot' ? spotOrders : futuresOrders;
        const title = activeTab === 'spot' ? 'Spot Ордери' : 'Futures Ордери';
        const icon = activeTab === 'spot' ? '📋' : '📈';

        // Якщо масив дорівнює null або баланс ще вантажиться
        // для точного визначення завантаження можна перевіряти стан
        if (!balance) {
            return (
                <div className="analytics-card orders-card">
                    <div className="orders-header-tabs">
                        <button
                            className={`tab-button ${activeTab === 'spot' ? 'active' : ''}`}
                            onClick={() => setActiveTab('spot')}
                        >
                            Spot
                        </button>
                        <button
                            className={`tab-button ${activeTab === 'futures' ? 'active' : ''}`}
                            onClick={() => setActiveTab('futures')}
                        >
                            Futures
                        </button>
                    </div>

                    <h3>{icon} {title}</h3>
                    <div className="loading-spinner">Завантаження ордерів...</div>
                </div>
            );
        }

        return (
            <div className="analytics-card orders-card">
                <div className="orders-header-tabs">
                    <button
                        className={`tab-button ${activeTab === 'spot' ? 'active' : ''}`}
                        onClick={() => setActiveTab('spot')}
                    >
                        Spot
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'futures' ? 'active' : ''}`}
                        onClick={() => setActiveTab('futures')}
                    >
                        Futures
                    </button>
                </div>

                <h3>{icon} {title} ({currentOrders.length})</h3>

                {currentOrders.length === 0 ? (
                    <div className="no-data">Немає активних ордерів</div>
                ) : (
                    <div className="orders-list">
                        {currentOrders.map((order, idx) => (
                            <div key={order.orderId || idx} className="order-item">
                                <div className="order-header">
                                    <span className="order-symbol">{order.symbol}</span>
                                    <span className={`order-side ${order.side.toLowerCase()}`}>{order.side}</span>
                                </div>
                                <div className="order-details">
                                    <div className="detail-row">
                                        <span>Ціна:</span>
                                        <span>{order.price}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span>Кількість:</span>
                                        <span>{order.qty}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span>Тип:</span>
                                        <span>{order.orderType}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // --- Головний Render ---
    return (
        <>
            <Navbar />
            <div className="analytics-page">
                {loading ? (
                    <div className="analytics-loading">
                        <div className="spinner"></div>
                        <p>Завантаження даних...</p>
                    </div>
                ) : (
                    <div className="analytics-container">
                        {error && <div className="analytics-error">{error}</div>}

                        {exchanges.length === 0 && banks.length === 0 ? (
                            <div className="analytics-card analytics-card--full">
                                <div className="empty-state">
                                    <div className="empty-icon">🔌</div>
                                    <h3>Нічого не підключено</h3>
                                    <p>Перейдіть в налаштування профілю, щоб додати API ключі бірж або банку для збору аналітики.</p>
                                </div>
                            </div>
                        ) : (
                            <>
                                {exchanges.length > 0 && (
                                    <>
                                        {/* Секція Біржі */}
                                        <div className="analytics-header">
                                            <h1 className="analytics-title">📊 Аналітика Біржі</h1>
                                            {renderExchangeSelector()}
                                        </div>

                                        <div className="analytics-grid">
                                            {renderBalance()}
                                            {renderOrders()}
                                        </div>
                                    </>
                                )}

                                {banks.length > 0 && (
                                    <>
                                        {/* Секція Банку */}
                        <div className="analytics-header analytics-header--bank">
                            <h1 className="analytics-title">🏦 Аналітика Банку</h1>

                            {/* Фільтр по підключеним банкам */}
                            {banks.length > 0 && (
                                <div className="bank-account-chips">
                                    {banks.map(b => (
                                        <button
                                            key={b.id}
                                            className={`account-chip ${selectedBankId === b.id ? 'account-chip--active' : ''}`}
                                            onClick={() => setSelectedBankId(b.id)}
                                        >
                                            🏦 {b.name || b.bank_name}
                                        </button>
                                    ))}
                                </div>
                            )}

                            <div className="month-picker">
                                <button
                                    className="month-nav-btn"
                                    onClick={() => {
                                        if (selectedMonth === 0) { setSelectedMonth(11); setSelectedYear(y => y - 1); }
                                        else setSelectedMonth(m => m - 1);
                                    }}
                                >‹</button>
                                <span className="month-label">
                                    {MONTHS_UK[selectedMonth]} {selectedYear}
                                </span>
                                <button
                                    className="month-nav-btn"
                                    disabled={selectedMonth === now.getMonth() && selectedYear === now.getFullYear()}
                                    onClick={() => {
                                        if (selectedMonth === 11) { setSelectedMonth(0); setSelectedYear(y => y + 1); }
                                        else setSelectedMonth(m => m + 1);
                                    }}
                                >›</button>
                            </div>
                        </div>

                        {bankLoading ? (
                            <div className="analytics-card analytics-card--full analytics-card--bank" style={{ textAlign: 'center', padding: '40px' }}>
                                <div className="spinner"></div>
                                <p style={{ color: '#94a3b8', marginTop: '12px' }}>
                                    Завантаження даних за {MONTHS_UK[selectedMonth]} {selectedYear}...
                                </p>
                            </div>
                        ) : bankAnalytics ? (
                            <>
                                <div className="analytics-grid">
                                    {/* Поточний баланс */}
                                    <div className="analytics-card analytics-card--bank">
                                        <div className="card-icon">💳</div>
                                        <h3 className="card-title">Поточний баланс</h3>
                                        <div className="balance-amount">
                                            {bankAnalytics.balance.toFixed(2)} UAH
                                        </div>
                                        <div className="balance-change">
                                            <span className="negative">
                                                ↓ {bankAnalytics.expenses.toFixed(2)} UAH
                                            </span>
                                            <span className="change-label">витрат за місяць</span>
                                        </div>
                                    </div>

                                    {/* Доходи/Витрати */}
                                    <div className="analytics-card analytics-card--bank">
                                        <div className="card-icon">📊</div>
                                        <h3 className="card-title">Доходи та Витрати</h3>
                                        <div className="income-expenses">
                                            <div className="income-row">
                                                <span className="label">Доходи:</span>
                                                <span className="value positive">+{bankAnalytics.income.toFixed(2)} UAH</span>
                                            </div>
                                            <div className="expense-row">
                                                <span className="label">Витрати:</span>
                                                <span className="value negative">-{bankAnalytics.expenses.toFixed(2)} UAH</span>
                                            </div>
                                            <div className="savings-row">
                                                <span className="label">Коефіцієнт заощаджень:</span>
                                                <span className="value">{bankAnalytics.savingsRate}%</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Прогноз балансу (ForecastAgent) */}
                                    <div className="analytics-card analytics-card--bank">
                                        <div className="card-icon">🔮</div>
                                        <h3 className="card-title">
                                            Прогноз на 30 днів
                                            <span className="agent-badge">AI Регресія</span>
                                        </h3>
                                        {forecastLoading ? (
                                            <div className="ai-loading">
                                                <div className="spinner-sm" />
                                                Розрахунок прогнозу...
                                            </div>
                                        ) : forecastData?.data ? (
                                            <>
                                                <div className="forecast-grid">
                                                    <div className="forecast-item">
                                                        <div className="forecast-label">Доходи</div>
                                                        <div className="forecast-value positive">
                                                            +{forecastData.data.forecast_income.toLocaleString('uk-UA')}
                                                        </div>
                                                        <div className={`forecast-trend ${forecastData.data.inc_trend >= 0 ? 'up' : 'down'}`}>
                                                            {forecastData.data.inc_trend >= 0 ? '↑' : '↓'} {Math.abs(forecastData.data.inc_trend).toFixed(0)} {forecastData.data.inc_trend_unit === 'month' ? 'грн/міс' : 'грн/тиж'}
                                                        </div>
                                                    </div>
                                                    <div className="forecast-item">
                                                        <div className="forecast-label">Витрати</div>
                                                        <div className="forecast-value negative">
                                                            −{forecastData.data.forecast_expense.toLocaleString('uk-UA')}
                                                        </div>
                                                        <div className={`forecast-trend ${forecastData.data.exp_trend > 0 ? 'down' : 'up'}`}>
                                                            {forecastData.data.exp_trend > 0 ? '↑' : '↓'} {Math.abs(forecastData.data.exp_trend).toFixed(0)} грн/тиж
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="forecast-balance">
                                                    {forecastData.data.forecast_balance >= 0 ? '+' : ''}
                                                    {forecastData.data.forecast_balance.toLocaleString('uk-UA')} UAH
                                                </div>
                                                {(() => {
                                                    const totalWeeks = (forecastData.data.accuracy?.expenses?.train_weeks ?? 0) +
                                                                       (forecastData.data.accuracy?.expenses?.test_weeks ?? 0);
                                                    const expR2 = forecastData.data.accuracy?.expenses?.r2 ?? 0;
                                                    const incR2 = forecastData.data.accuracy?.income?.r2 ?? 0;

                                                    const r2Label = (r2) => {
                                                        if (r2 >= 0.7) return { text: 'висока', cls: 'r2-high' };
                                                        if (r2 >= 0.4) return { text: 'задовільна', cls: 'r2-mid' };
                                                        if (r2 >= 0.0) return { text: 'низька', cls: 'r2-low' };
                                                        return { text: 'нестабільна', cls: 'r2-low' };
                                                    };
                                                    const r2Display = (r2) => r2 < 0 ? '< 0' : r2.toFixed(3);

                                                    if (totalWeeks < 8) {
                                                        return (
                                                            <div className="accuracy-section">
                                                                <div className="forecast-low-data-hint">
                                                                    ⚠️ Прогноз орієнтовний — недостатньо даних ({totalWeeks} тижн.). Для надійного результату потрібно 8+ тижнів транзакцій.
                                                                </div>
                                                            </div>
                                                        );
                                                    }

                                                    const expLbl = r2Label(expR2);
                                                    const incLbl = r2Label(incR2);

                                                    return (
                                                        <div className="accuracy-section">
                                                            <div className="accuracy-title">Точність моделі</div>
                                                            <div className="accuracy-grid">
                                                                <div className="accuracy-item">
                                                                    <div className="accuracy-label">R² витрат</div>
                                                                    <div className={`accuracy-metric ${expLbl.cls}`}>
                                                                        {r2Display(expR2)}{' '}
                                                                        <span className="r2-label-text">({expLbl.text})</span>
                                                                    </div>
                                                                </div>
                                                                <div className="accuracy-item">
                                                                    <div className="accuracy-label">
                                                                        R² доходів
                                                                        {forecastData.data.inc_aggregation && (
                                                                            <span className="agg-badge">{forecastData.data.inc_aggregation}</span>
                                                                        )}
                                                                    </div>
                                                                    <div className={`accuracy-metric ${incLbl.cls}`}>
                                                                        {r2Display(incR2)}{' '}
                                                                        <span className="r2-label-text">({incLbl.text})</span>
                                                                    </div>
                                                                </div>
                                                                <div className="accuracy-item">
                                                                    <div className="accuracy-label">MAE витрат</div>
                                                                    <div className="accuracy-metric">
                                                                        {forecastData.data.accuracy.expenses.mae != null
                                                                            ? `${forecastData.data.accuracy.expenses.mae.toLocaleString('uk-UA')} грн`
                                                                            : '—'}
                                                                    </div>
                                                                </div>
                                                                <div className="accuracy-item">
                                                                    <div className="accuracy-label">Тижнів даних</div>
                                                                    <div className="accuracy-metric">{totalWeeks}</div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                })()}
                                            </>
                                        ) : (
                                            <div className="forecast-info">
                                                <div className="forecast-balance">
                                                    {bankAnalytics.forecastBalance} UAH
                                                </div>
                                                <p className="forecast-hint">
                                                    При середніх витратах {bankAnalytics.averageDailyExpenses} UAH/день
                                                </p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Розподіл витрат — donut chart */}
                                    {(() => {
                                        const cats = bankAnalytics.topCategories;
                                        const total = cats.reduce((s, c) => s + c.amount, 0);
                                        if (!cats.length || total === 0) return null;

                                        const colors = ['#667eea', '#a78bfa', '#4ade80', '#fbbf24', '#f87171'];
                                        const r = 46;
                                        const circ = 2 * Math.PI * r;
                                        let cumPct = 0;

                                        const slices = cats.map((cat, i) => {
                                            const pct = cat.amount / total;
                                            const rotation = -90 + cumPct * 360;
                                            cumPct += pct;
                                            return { ...cat, pct, rotation, color: colors[i % colors.length] };
                                        });

                                        return (
                                            <div className="analytics-card analytics-card--bank donut-card">
                                                <div className="card-icon">🍩</div>
                                                <h3 className="card-title">Розподіл витрат</h3>
                                                <div className="donut-body">
                                                    <div className="donut-chart-wrap" style={{ position: 'relative' }}>
                                                        <svg width="132" height="132" viewBox="0 0 132 132">
                                                            {slices.map((s, i) => (
                                                                <circle key={i}
                                                                    cx="66" cy="66" r={r}
                                                                    fill="none"
                                                                    stroke={s.color}
                                                                    strokeWidth={hoveredSliceIdx === i ? "24" : "20"}
                                                                    strokeDasharray={`${s.pct * circ * 0.95} ${circ}`}
                                                                    transform={`rotate(${s.rotation} 66 66)`}
                                                                    onMouseEnter={() => setHoveredSliceIdx(i)}
                                                                    onMouseLeave={() => setHoveredSliceIdx(null)}
                                                                    style={{ cursor: 'pointer', transition: 'stroke-width 0.2s', opacity: hoveredSliceIdx !== null && hoveredSliceIdx !== i ? 0.6 : 1 }}
                                                                />
                                                            ))}
                                                            <circle cx="66" cy="66" r="30" fill="rgba(30,41,59,0.95)" />
                                                            <text x="66" y="58" textAnchor="middle"
                                                                fill="#94a3b8" fontSize="9" fontFamily="inherit">
                                                                {hoveredSliceIdx !== null ? slices[hoveredSliceIdx].name.slice(0, 12) : 'UAH'}
                                                            </text>
                                                            <text x="66" y="75" textAnchor="middle"
                                                                fill="#f1f5f9" fontSize="12" fontWeight="800"
                                                                fontFamily="inherit">
                                                                {hoveredSliceIdx !== null 
                                                                    ? slices[hoveredSliceIdx].amount.toLocaleString('uk-UA', { maximumFractionDigits: 0 }) 
                                                                    : total.toLocaleString('uk-UA', { maximumFractionDigits: 0 })}
                                                            </text>
                                                        </svg>
                                                    </div>
                                                    <div className="donut-legend">
                                                        {slices.map((s, i) => (
                                                            <div key={i} 
                                                                className="donut-legend-item"
                                                                onMouseEnter={() => setHoveredLegendIdx(i)}
                                                                onMouseLeave={() => setHoveredLegendIdx(null)}
                                                                style={{ cursor: 'pointer' }}
                                                            >
                                                                <span className="donut-dot" style={{ background: s.color }} />
                                                                <span className="donut-legend-name">
                                                                    {s.name.length > 16 ? s.name.slice(0, 16) + '…' : s.name}
                                                                </span>
                                                                <span className="donut-legend-pct">
                                                                    {hoveredLegendIdx === i
                                                                        ? `${s.amount.toLocaleString('uk-UA', { maximumFractionDigits: 0 })} ₴` 
                                                                        : `${(s.pct * 100).toFixed(0)}%`}
                                                                </span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })()}
                                </div>

                                {/* AI Аналіз прогнозу — повна ширина */}
                                {forecastData?.forecast && (
                                    <div className="ai-forecast-card" style={{ marginBottom: '35px' }}>
                                        <div className="ai-forecast-header">
                                            <div className="ai-forecast-icon">🤖</div>
                                            <div className="ai-forecast-meta">
                                                <h3 className="ai-forecast-title">AI Аналіз прогнозу</h3>
                                            </div>
                                        </div>
                                        <div className="ai-forecast-body">
                                            <div className="ai-text">{renderForecastText(forecastData.forecast)}</div>
                                        </div>
                                    </div>
                                )}

                                {/* Графік витрат */}
                                <div className="analytics-card analytics-card--full analytics-card--bank" style={{ marginBottom: '35px' }}>
                                    <div className="card-icon">📉</div>
                                    <h3 className="card-title">Динаміка надходжень та витрат (поточний місяць)</h3>
                                    <div style={{ width: '100%', height: 300 }}>
                                        <ResponsiveContainer>
                                            <BarChart data={bankAnalytics.chartData}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                                                <XAxis
                                                    dataKey="name"
                                                    stroke="#94a3b8"
                                                    tick={{ fill: '#94a3b8', fontSize: 12 }}
                                                    tickLine={false}
                                                    axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                                                />
                                                <YAxis
                                                    stroke="#94a3b8"
                                                    tick={{ fill: '#94a3b8', fontSize: 12 }}
                                                    tickLine={false}
                                                    axisLine={false}
                                                    width={60}
                                                />
                                                <Tooltip
                                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
                                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                                    formatter={(value, name) => [
                                                        `${parseFloat(value).toFixed(2)} UAH`,
                                                        name === 'income' ? 'Надходження' : 'Витрати'
                                                    ]}
                                                />
                                                <Bar dataKey="income" name="income" fill="#4ade80" radius={[4, 4, 0, 0]} />
                                                <Bar dataKey="expense" name="expense" fill="#f87171" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                            </>
                        ) : null}
                                    </>
                                )}
                            </>
                        )}

                    </div>
                )}
            </div>
        </>
    );
}

export default Analytics;
