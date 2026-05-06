import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { authService } from '../api/authService';
import { useFinance } from '../context/FinanceContext';
import '../styles/dashboardStyles.css';

function calcMonthStats(txList) {
	const now = new Date();
	let income = 0;
	let expense = 0;
	txList.forEach(t => {
		if (t.type === 'transfer') return;
		const d = t.transaction_date || t.date || t.time;
		const parsed = d ? new Date(d) : null;
		if (!parsed || isNaN(parsed.getTime())) return;
		if (parsed.getMonth() !== now.getMonth() || parsed.getFullYear() !== now.getFullYear()) return;
		const amount = parseFloat(t.amount) || 0;
		if (t.type === 'income') income += amount;
		else if (t.type === 'expense') expense += Math.abs(amount);
	});
	return { income, expense };
}

function Dashboard() {
	const navigate = useNavigate();
	const { getBalance, getTransactions } = useFinance();
	const [userName, setUserName] = useState('');
	const [balance, setBalance] = useState(null);
	const [stats, setStats] = useState(null);
	const [transactions, setTransactions] = useState([]);
	const [loadingBalance, setLoadingBalance] = useState(true);
	const [loadingTx, setLoadingTx] = useState(true);

	useEffect(() => {
		const token = localStorage.getItem('token');
		if (!token) { navigate('/login'); return; }

		// Ім'я профілю
		const saved = JSON.parse(localStorage.getItem('user_profile') || '{}');
		if (saved.first_name) setUserName(saved.first_name);
		authService.getMe(token)
			.then(u => setUserName(u.first_name || u.username || 'Користувачу'))
			.catch(() => {});

		// Баланс — з кешу або API
		getBalance()
			.then(res => {
				if (res) setBalance(res.balance ?? res.total_balance ?? 0);
			})
			.catch(() => setBalance(0))
			.finally(() => setLoadingBalance(false));

		// Транзакції + статистика — з кешу або API
		getTransactions('all', 31)
			.then(res => {
				const list = Array.isArray(res) ? res : (Array.isArray(res?.transactions) ? res.transactions : []);
				setStats(calcMonthStats(list));
				setTransactions(list.slice(0, 5));
			})
			.catch(() => setStats({ income: 0, expense: 0 }))
			.finally(() => setLoadingTx(false));
	}, [navigate, getBalance, getTransactions]);

	const fmt = (n) => (Number(n) || 0).toLocaleString('uk-UA');

	return (
		<div className="dashboard-wrapper">
			<Navbar />

			<div className="dashboard-container">
				<div className="dashboard-main-box dashboard-layout">

					<div className="dashboard-header">
						<h1 className="dashboard-title">Привіт, {userName || 'Користувачу'}! 👋</h1>
						<p className="dashboard-subtitle">Ось ваш фінансовий зріз на сьогодні</p>
					</div>

					{/* Баланс + статистика */}
					<div className="dashboard-summary-section">
						<div className="dashboard-total-card">
							<h2>Загальний баланс</h2>
							<div className="balance-info">
								{loadingBalance
									? <p className="loading-inline">Завантаження...</p>
									: <h1 className="balance-amount">{fmt(balance)} ₴</h1>
								}
							</div>
						</div>

						<div className="dashboard-quick-stats">
							<div className="stat-card income">
								<span className="stat-icon">⬆️</span>
								<div>
									<div className="stat-label">Доходи за місяць</div>
									{loadingTx
										? <div className="stat-value loading-inline">...</div>
										: <div className="stat-value">{fmt(stats?.income)} ₴</div>
									}
								</div>
							</div>
							<div className="stat-card expense">
								<span className="stat-icon">⬇️</span>
								<div>
									<div className="stat-label">Витрати за місяць</div>
									{loadingTx
										? <div className="stat-value loading-inline">...</div>
										: <div className="stat-value">{fmt(stats?.expense)} ₴</div>
									}
								</div>
							</div>
						</div>
					</div>

					<div className="dashboard-grid-2-col">
						{/* Останні транзакції */}
						<div className="dashboard-widget recent-transactions">
							<div className="widget-header">
								<h3>💳 Останні транзакції</h3>
								<Link to="/transactions" className="widget-link">Всі транзакції →</Link>
							</div>

							<div className="transaction-list">
								{loadingTx && <p>Завантаження...</p>}
								{!loadingTx && transactions.length === 0 && (
									<p className="no-data-text">
										Транзакції відсутні. Підключіть банк у <Link to="/profile">налаштуваннях</Link>.
									</p>
								)}
								{!loadingTx && transactions.map((tx, idx) => {
									const d = tx.transaction_date || tx.date || tx.time;
									const parsed = d ? new Date(d) : null;
									const dateStr = parsed && !isNaN(parsed) ? parsed.toLocaleDateString('uk-UA') : '—';
									const isTransfer = tx.type === 'transfer';
									const sign = tx.type === 'income' ? '+' : (isTransfer ? '↔' : '−');
									const amountClass = tx.type === 'income' ? 'positive' : (isTransfer ? 'neutral' : 'negative');

									return (
										<div key={idx} className={`tx-item tx-${tx.type || 'default'}`}>
											<div className="tx-info">
												<span className="tx-desc">{tx.description || 'Транзакція'}</span>
												<span className="tx-date">{dateStr}</span>
											</div>
											<span className={`tx-amount ${amountClass}`}>
												{sign}{Math.abs(tx.amount || 0).toLocaleString('uk-UA')} {tx.currency || '₴'}
											</span>
										</div>
									);
								})}
							</div>
						</div>

						{/* AI поради + швидкі дії */}
						<div className="dashboard-widget right-col">
							<div className="ai-insights">
								<h3>💡 AI Аналітика</h3>
								<div className="insight-box">
									<p>Скористайтесь чатом-помічником або перейдіть до детального аналізу ваших фінансів.</p>
								</div>
								<Link to="/analytics" className="widget-link ai-link">Детальний аналіз →</Link>
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
