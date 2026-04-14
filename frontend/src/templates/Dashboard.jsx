import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { authService } from '../api/authService';
import { financeService } from '../api/financeService';
import '../styles/dashboardStyles.css';

function Dashboard() {
	const navigate = useNavigate();
	const [userName, setUserName] = useState('');
	const [loading, setLoading] = useState(true);

	// Mock or state data
	const [balance, setBalance] = useState({ total: 0, currency: '₴', trend: '+0%' });
	const [stats, setStats] = useState({ income: 0, expense: 0 });
	const [transactions, setTransactions] = useState([]);
	const [aiInsight, setAiInsight] = useState('');

	useEffect(() => {
		const initDashboard = async () => {
			const token = localStorage.getItem('token');
			if (!token) {
				navigate('/login');
				return;
			}

			try {
				// Get User
				const savedUser = JSON.parse(localStorage.getItem('user_profile') || '{}');
				if (savedUser.first_name) setUserName(savedUser.first_name);

				try {
					const userData = await authService.getMe(token);
					setUserName(userData.first_name || userData.username || 'Користувачу');
				} catch (e) {
					console.error('Помилка завантаження профілю:', e);
				}

				// Get Analytics & Transactions & AI insights parameters asynchronously and individually
				// to avoid blocking the whole page load on one endpoint.
				const fetchAnalytics = async () => {
					try {
						const res = await financeService.getBankAnalytics(token);
						if (res) {
							// We let fetchTx handle income/expense to calculate cleanly.
							// Not reading from analytics summary to avoid conflict with pure month.
							setBalance({
								total: res.balance ?? res.total_balance ?? res.summary?.balance ?? 0,
								currency: '₴',
								trend: '+0%' // Keep mock or update if backend provides
							});
						}
					} catch (e) {
						console.error('Помилка завантаження банківської аналітики:', e);
					}
				};

				const fetchTx = async () => {
					try {
						// Беремо 31 день, щоб точно охопити поточний місяць
						const res = await financeService.getTransactions(token, 'all', 31);
						if (res && Array.isArray(res)) {
							// Calculate stats from ALL transactions for the CURRENT MONTH explicitly
							let calcIncome = 0;
							let calcExpense = 0;

							const now = new Date();
							const currentMonth = now.getMonth();
							const currentYear = now.getFullYear();

							res.forEach(t => {
								const txDateInfo = t.transaction_date || t.date || t.time;
								const parsedDate = txDateInfo ? new Date(txDateInfo) : null;

								if (parsedDate && parsedDate.getMonth() === currentMonth && parsedDate.getFullYear() === currentYear) {
									const amount = parseFloat(t.amount) || 0;
									if (t.type === 'income') calcIncome += amount;
									else if (t.type === 'expense') calcExpense += Math.abs(amount);
									else if (amount > 0) calcIncome += amount;
									else calcExpense += Math.abs(amount);
								}
							});

							// Only update if we didn't receive pre-calculated ones or to override
							setStats({
								income: calcIncome,
								expense: calcExpense
							});

							setTransactions(res.slice(0, 5));
						} else if (res && Array.isArray(res.transactions)) {
							let calcIncome = 0;
							let calcExpense = 0;

							const now = new Date();
							const currentMonth = now.getMonth();
							const currentYear = now.getFullYear();

							res.transactions.forEach(t => {
								const txDateInfo = t.transaction_date || t.date || t.time;
								const parsedDate = txDateInfo ? new Date(txDateInfo) : null;

								if (parsedDate && parsedDate.getMonth() === currentMonth && parsedDate.getFullYear() === currentYear) {
									const amount = parseFloat(t.amount) || 0;
									if (t.type === 'income') calcIncome += amount;
									else if (t.type === 'expense') calcExpense += Math.abs(amount);
									else if (amount > 0) calcIncome += amount;
									else calcExpense += Math.abs(amount);
								}
							});

							setStats({
								income: calcIncome,
								expense: calcExpense
							});

							setTransactions(res.transactions.slice(0, 5));
						}
					} catch (e) {
						console.error('Помилка завантаження транзакцій:', e);
					}
				};

				// Fire requests in parallel without await all (to let components update as data arrives)
				fetchAnalytics();
				fetchTx();

				// Keep AI static or add an independent fetch if needed 
				setAiInsight("Ваші фінанси синхронізовано. Слідкуйте за витратами на розваги в цьому місяці.");

			} catch (generalError) {
				console.error('Критична помилка ініціалізації дашборду:', generalError);
			} finally {
				// We drop loading early so UI can render the shell quickly
				setLoading(false);
			}
		};

		initDashboard();
	}, [navigate]);

	return (
		<div className="dashboard-wrapper">
			<Navbar />

			<div className="dashboard-container">
				<div className="dashboard-main-box dashboard-layout">

					<div className="dashboard-header">
						<h1 className="dashboard-title">Привіт, {userName || 'Користувачу'}! 👋</h1>
						<p className="dashboard-subtitle">Ось ваш фінансовий зріз на сьогодні</p>
					</div>

					{/* Верхній блок: Баланс */}
					<div className="dashboard-summary-section">
						<div className="dashboard-total-card">
							<h2>Загальний баланс</h2>
							<div className="balance-info">
								<h1 className="balance-amount">{(Number(balance.total) || 0).toLocaleString('uk-UA')} {balance.currency}</h1>
								{/* Placeholder for trend */}
								<span className="balance-trend positive">📈 +0 (за місяць)</span>
							</div>
						</div>

						<div className="dashboard-quick-stats">
							<div className="stat-card income">
								<span className="stat-icon">⬇️</span>
								<div>
									<div className="stat-label">Доходи за місяць</div>
									<div className="stat-value">{(Number(stats.income) || 0).toLocaleString('uk-UA')} ₴</div>
								</div>
							</div>
							<div className="stat-card expense">
								<span className="stat-icon">⬆️</span>
								<div>
									<div className="stat-label">Витрати за місяць</div>
									<div className="stat-value">{(Number(stats.expense) || 0).toLocaleString('uk-UA')} ₴</div>
								</div>
							</div>
						</div>
					</div>

					<div className="dashboard-grid-2-col">
						{/* Ліва колонка: Останні транзакції */}
						<div className="dashboard-widget recent-transactions">
							<div className="widget-header">
								<h3>💳 Останні транзакції</h3>
								<Link to="/transactions" className="widget-link">Всі транзакції &rarr;</Link>
							</div>

							<div className="transaction-list">
								{loading && <p>Завантаження...</p>}
								{!loading && transactions.length === 0 && (
									<p className="no-data-text">Транзакції відсутні або ще не синхронізовані.</p>
								)}
								{!loading && transactions.map((tx, idx) => {
									const txDate = tx.transaction_date || tx.date || tx.time;
									const parsedDate = txDate ? new Date(txDate) : null;
									const formattedDate = parsedDate && !isNaN(parsedDate.getTime())
										? parsedDate.toLocaleDateString('uk-UA')
										: 'Невідома дата';

									return (
										<div key={idx} className={`tx-item tx-${tx.type || 'default'}`}>
											<div className="tx-info">
												<span className="tx-desc">{tx.description || tx.type || 'Транзакція'}</span>
												<span className="tx-date">{formattedDate}</span>
											</div>
											<span className={`tx-amount ${tx.type === 'expense' || tx.amount < 0 ? 'negative' : 'positive'}`}>
												{tx.type === 'income' ? '+' : (tx.type === 'expense' ? '-' : ((tx.amount || 0) > 0 ? '+' : '-'))}{Math.abs(tx.amount || 0)} {tx.currency || '₴'}
											</span>
										</div>
									);
								})}
							</div>
						</div>

						{/* Права колонка: AI поради / Швидкі дії */}
						<div className="dashboard-widget right-col">
							<div className="ai-insights">
								<h3>💡 AI Аналітика</h3>
								<div className="insight-box">
									<p>{aiInsight}</p>
								</div>
								<Link to="/analytics" className="widget-link ai-link">Детальний аналіз &rarr;</Link>
							</div>

							<div className="quick-actions">
								<h3>⚡ Швидкі дії</h3>
								<div className="action-buttons">
									<Link to="/profile" className="action-btn">🏦 Підключити банк</Link>
									<Link to="/profile" className="action-btn">🔑 Підключити біржу</Link>
								</div>
							</div>
						</div>
					</div>

				</div>
			</div>
		</div>
	);
}

export default Dashboard;
