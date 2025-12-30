import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { financeService } from '../api/financeService';
import '../styles/analyticsStyles.css';

function Analytics() {
	const [selectedExchange, setSelectedExchange] = useState('BYBIT');
	const [exchangeBalance, setExchangeBalance] = useState(null);
	const [bankBalance, setBankBalance] = useState(null);
	const [bankAnalytics, setBankAnalytics] = useState(null);
	const [orders, setOrders] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const navigate = useNavigate();

	useEffect(() => {
		fetchAnalytics();
	}, [selectedExchange]);

	const fetchAnalytics = async () => {
		try {
			const token = localStorage.getItem('token');
			if (!token) {
				navigate('/login');
				return;
			}

			setLoading(true);
			setError('');

			// Завантажуємо дані біржі
			try {
				const balanceData = await financeService.getExchangeBalance(token, selectedExchange.toLowerCase());
				setExchangeBalance(balanceData);
			} catch (err) {
				console.error('Помилка завантаження балансу біржі:', err);
			}

			// Завантажуємо дані банку
			try {
				const bankData = await financeService.getBankAnalytics(token);
				setBankBalance(bankData);
				
				// Розраховуємо аналітику
				const analytics = calculateBankAnalytics(bankData);
				setBankAnalytics(analytics);
			} catch (err) {
				console.error('Помилка завантаження банківської аналітики:', err);
			}

			// Завантажуємо ордери
			try {
				const ordersData = await financeService.getExchangeOrders(token, selectedExchange.toLowerCase(), 'spot');
				setOrders(ordersData);
			} catch (err) {
				console.error('Помилка завантаження ордерів:', err);
			}

		} catch (err) {
			console.error('Помилка завантаження аналітики:', err);
			setError(err.message || 'Помилка завантаження даних');
		} finally {
			setLoading(false);
		}
	};

	const calculateBankAnalytics = (bankData) => {
		if (!bankData || !bankData.transactions) return null;

		const now = new Date();
		const monthAgo = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());

		// Фільтруємо транзакції за останній місяць
		const monthTransactions = bankData.transactions.filter(t => 
			new Date(t.transaction_date) >= monthAgo
		);

		// Рахуємо доходи та витрати
		const income = monthTransactions
			.filter(t => t.type === 'income')
			.reduce((sum, t) => sum + parseFloat(t.amount), 0);

		const expenses = monthTransactions
			.filter(t => t.type === 'expense')
			.reduce((sum, t) => sum + parseFloat(t.amount), 0);

		// Топ категорій витрат
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

		// Прогноз балансу на наступний місяць
		const averageDailyExpenses = expenses / 30;
		const forecastBalance = bankData.balance - (averageDailyExpenses * 30);

		// Рекомендація для інвестування
		const safeAmount = bankData.balance * 0.3; // 30% від балансу
		const recommendedInvestment = Math.max(0, safeAmount);

		return {
			balance: bankData.balance,
			income,
			expenses,
			netIncome: income - expenses,
			topCategories,
			averageDailyExpenses: averageDailyExpenses.toFixed(2),
			forecastBalance: forecastBalance.toFixed(2),
			recommendedInvestment: recommendedInvestment.toFixed(2),
			savingsRate: income > 0 ? ((income - expenses) / income * 100).toFixed(1) : 0
		};
	};

	if (loading) {
		return (
			<>
				<Navbar />
				<div className="analytics-loading">
					<div className="spinner"></div>
					<p>Завантаження аналітики...</p>
				</div>
			</>
		);
	}

	return (
		<>
			<Navbar />
			<div className="analytics-page">
				<div className="analytics-container">
					<div className="analytics-header">
						<h1 className="analytics-title">📊 Аналітика Біржі</h1>
						<select
							value={selectedExchange}
							onChange={(e) => setSelectedExchange(e.target.value)}
							className="exchange-select"
						>
							<option value="BYBIT">BYBIT</option>
							<option value="BINANCE">BINANCE</option>
							<option value="OKX">OKX</option>
						</select>
					</div>

					{error && <div className="analytics-error">{error}</div>}

					{/* Аналітика біржі */}
					<div className="analytics-grid">
						{/* Баланс біржі */}
						<div className="analytics-card">
							<div className="card-icon">💰</div>
							<h3 className="card-title">Баланс ({selectedExchange})</h3>
							{exchangeBalance ? (
								<div className="balance-info">
									<p className="balance-hint">Немає даних про баланс</p>
								</div>
							) : (
								<p className="balance-hint">Підключіть біржу в налаштуваннях</p>
							)}
						</div>

						{/* Spot ордери */}
						<div className="analytics-card">
							<div className="card-icon">📋</div>
							<h3 className="card-title">Spot Ордери ({orders?.result?.list?.length || 0})</h3>
							{orders?.result?.list?.length > 0 ? (
								<div className="orders-list">
									{orders.result.list.slice(0, 3).map((order, idx) => (
										<div key={idx} className="order-item">
											<span className="order-symbol">{order.symbol}</span>
											<span className="order-amount">{order.qty}</span>
										</div>
									))}
								</div>
							) : (
								<p className="balance-hint">Немає активних ордерів</p>
							)}
						</div>
					</div>

					{/* Аналітика банку */}
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
										<span className={bankAnalytics.netIncome >= 0 ? 'positive' : 'negative'}>
											{bankAnalytics.netIncome >= 0 ? '↑' : '↓'} {Math.abs(bankAnalytics.netIncome).toFixed(2)} UAH
										</span>
										<span className="change-label">за місяць</span>
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
			</div>
		</>
	);
}

export default Analytics;
