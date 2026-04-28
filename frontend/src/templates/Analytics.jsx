import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Navbar from '../components/Navbar';
import { financeService } from '../api/financeService';
import '../styles/analyticsStyles.css';

function Analytics() {
    // --- State для Біржі ---
    const [exchanges, setExchanges] = useState([]);
    const [selectedExchange, setSelectedExchange] = useState('');
    const [balance, setBalance] = useState(null);
    const [spotOrders, setSpotOrders] = useState([]);
    const [futuresOrders, setFuturesOrders] = useState([]);
    const [activeTab, setActiveTab] = useState('spot');

    // --- State для Банку ---
    const [bankAnalytics, setBankAnalytics] = useState(null);

    // --- Загальний State ---
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    // 1. Завантаження списку бірж та банківських даних при старті
    useEffect(() => {
        const initData = async () => {
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            setLoading(true);
            setError('');
            
            const fetchExchanges = financeService.getExchanges(token)
                .then(exchangesList => {
                    setExchanges(exchangesList);
                    if (exchangesList && exchangesList.length > 0) {
                        setSelectedExchange(exchangesList[0].exchange_name);
                    } else {
                        setExchanges([]); 
                    }
                })
                .catch(err => {
                    console.error('Помилка завантаження списку бірж:', err);
                    setError('Не вдалося завантажити список бірж');
                });

            const fetchBankData = financeService.getBankAnalytics(token)
                .then(bankData => {
                    const analytics = calculateBankAnalytics(bankData);
                    setBankAnalytics(analytics);
                })
                .catch(err => {
                    console.error('Помилка завантаження банківської аналітики:', err);
                    setError(prev => prev ? `${prev}. Не вдалося завантажити банківські дані` : 'Не вдалося завантажити банківські дані');
                });

            // Паралельне завантаження
            await Promise.all([fetchExchanges, fetchBankData]);

            setLoading(false);
        };

        initData();
    }, [navigate]);

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
                .then(data => setBalance(data))
                .catch(err => {
                    console.error(`Помилка завантаження балансу для ${selectedExchange}:`, err);
                    setBalance(null);
                });

            const spotPromise = financeService.getExchangeOrders(token, selectedExchange, 'spot')
                .then(data => setSpotOrders(data?.result?.list || data?.list || []))
                .catch(err => {
                    console.error(`Помилка завантаження Spot ордерів для ${selectedExchange}:`, err);
                    setSpotOrders([]);
                });

            const futuresPromise = financeService.getExchangeOrders(token, selectedExchange, 'linear') // 'linear' для Bybit futures
                .then(data => setFuturesOrders(data?.result?.list || data?.list || []))
                .catch(err => {
                    console.warn(`Futures ордери недоступні або сталася помилка для ${selectedExchange}:`, err);
                    setFuturesOrders([]);
                });

            await Promise.all([balancePromise, spotPromise, futuresPromise]);
        };

        fetchExchangeData();
    }, [selectedExchange]);

    // --- Логіка розрахунку банківської аналітики (без змін) ---
    const calculateBankAnalytics = (bankData) => {
        if (!bankData || !bankData.transactions) return null;

        const now = new Date();
        // Встановлюємо дату на початок поточного місяця (1 число)
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

        const monthTransactions = bankData.transactions.filter(t => 
            new Date(t.transaction_date) >= startOfMonth
        );

        const income = monthTransactions
            .filter(t => t.type === 'income')
            .reduce((sum, t) => sum + parseFloat(t.amount), 0);

        const expenses = monthTransactions
            .filter(t => t.type === 'expense')
            .reduce((sum, t) => sum + parseFloat(t.amount), 0);

        // Підготовка даних для графіку витрат та надходжень по днях
        const chartData = [];
        const daysInMonth = now.getDate(); // Показуємо дні до сьогодні
        
        for (let i = 1; i <= daysInMonth; i++) {
            chartData.push({ name: `${i}`, expense: 0, income: 0 });
        }

        monthTransactions.forEach(t => {
            const day = new Date(t.transaction_date).getDate();
            // Упевнимося, що транзакція потрапляє в діапазон
            if (day <= daysInMonth && chartData[day - 1]) {
                if (t.type === 'expense') {
                    chartData[day - 1].expense += parseFloat(t.amount);
                } else if (t.type === 'income') {
                    chartData[day - 1].income += parseFloat(t.amount);
                }
            }
        });

        const categoryExpenses = {};
        monthTransactions
            .filter(t => t.type === 'expense')
            .forEach(t => {
                const category = t.counterparty || 'Інше';
                categoryExpenses[category] = (categoryExpenses[category] || 0) + parseFloat(t.amount);
            });

        const topCategories = Object.entries(categoryExpenses)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([name, amount]) => ({ name, amount }));

        const averageDailyExpenses = expenses / 30;
        const forecastBalance = bankData.balance - (averageDailyExpenses * 30);
        const safeAmount = bankData.balance * 0.3;
        const recommendedInvestment = Math.max(0, safeAmount);

        return {
            balance: bankData.balance,
            income,
            expenses,
            netIncome: income - expenses,
            topCategories,
            chartData,
            averageDailyExpenses: averageDailyExpenses.toFixed(2),
            forecastBalance: forecastBalance.toFixed(2),
            recommendedInvestment: recommendedInvestment.toFixed(2),
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
                        
                        {/* Секція Біржі */}
                        <div className="analytics-header">
                            <h1 className="analytics-title">📊 Аналітика Біржі</h1>
                            {renderExchangeSelector()}
                        </div>

                        {error && <div className="analytics-error">{error}</div>}

                        {exchanges.length > 0 ? (
                            <div className="analytics-grid">
                                {renderBalance()}
                                {renderOrders()}
                            </div>
                        ) : (
                            <div className="analytics-card analytics-card--full">
                                <div className="empty-state">
                                    <div className="empty-icon">📉</div>
                                    <h3>Біржі не підключено</h3>
                                    <p>Перейдіть в налаштування профілю, щоб додати API ключі біржі.</p>
                                </div>
                            </div>
                        )}

                        {/* Секція Банку */}
                        <div className="analytics-header analytics-header--bank">
                            <h1 className="analytics-title">🏦 Аналітика Банку</h1>
                        </div>

                        {bankAnalytics ? (
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

                                    {/* Прогноз балансу */}
                                    <div className="analytics-card analytics-card--bank">
                                        <div className="card-icon">🔮</div>
                                        <h3 className="card-title">Прогноз на місяць</h3>
                                        <div className="forecast-info">
                                            <div className="forecast-balance">
                                                {bankAnalytics.forecastBalance} UAH
                                            </div>
                                            <p className="forecast-hint">
                                                При середніх витратах {bankAnalytics.averageDailyExpenses} UAH/день
                                            </p>
                                        </div>
                                    </div>
                                </div>

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

                                {/* Топ категорій витрат */}
                                <div className="analytics-card analytics-card--full analytics-card--bank">
                                    <div className="card-icon">📈</div>
                                    <h3 className="card-title">Топ-5 Категорій Витрат</h3>
                                    <div className="categories-list">
                                        {bankAnalytics.topCategories.map((cat, idx) => (
                                            <div key={idx} className="category-item">
                                                <div className="category-info">
                                                    <span className="category-name">{cat.name}</span>
                                                    <span className="category-amount">{cat.amount.toFixed(2)} UAH</span>
                                                </div>
                                                <div className="category-bar">
                                                    <div 
                                                        className="category-progress" 
                                                        style={{ width: `${(cat.amount / bankAnalytics.expenses * 100)}%` }}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Рекомендації інвестування */}
                                <div className="analytics-card analytics-card--full analytics-card--recommendation">
                                    <div className="card-icon">💡</div>
                                    <h3 className="card-title">Рекомендації для Інвестування</h3>
                                    <div className="recommendation-content">
                                        <div className="recommendation-item">
                                            <span className="recommendation-label">Рекомендована сума для інвестування:</span>
                                            <span className="recommendation-value">{bankAnalytics.recommendedInvestment} UAH</span>
                                        </div>
                                        <div className="recommendation-hint">
                                            💡 Рекомендуємо інвестувати не більше 30% від вашого балансу для диверсифікації ризиків
                                        </div>
                                        <div className="recommendation-actions">
                                            <button className="recommendation-btn recommendation-btn--primary">
                                                📊 Переглянути стратегії
                                            </button>
                                            <button className="recommendation-btn recommendation-btn--secondary">
                                                💰 Перевести на біржу
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="analytics-card analytics-card--full analytics-card--bank">
                                <div className="empty-state">
                                    <div className="empty-icon">🏦</div>
                                    <h3>Немає даних про банківський рахунок</h3>
                                    <p>Додайте банк в налаштуваннях профілю для відображення аналітики</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </>
    );
}

export default Analytics;
