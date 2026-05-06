import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useFinance } from '../context/FinanceContext';
import '../styles/transactionsStyles.css';

function Transactions() {
	const [transactions, setTransactions] = useState([]);
	const [filteredTransactions, setFilteredTransactions] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [filters, setFilters] = useState({
		search: '',
		type: 'all',
		source: 'all',
		dateFrom: '',
		dateTo: '',
	});
	const navigate = useNavigate();
	const { getTransactions } = useFinance();

	const fetchTransactions = useCallback(async () => {
		try {
			const token = localStorage.getItem('token');
			if (!token) { navigate('/login'); return; }

			// Дані з кешу або API (повторний перехід = миттєво)
			const data = await getTransactions(
				filters.source,
				30,
				filters.dateFrom,
				filters.dateTo
			);
			setTransactions(data);
			setFilteredTransactions(data);
		} catch (err) {
			setError(err.message || 'Помилка завантаження транзакцій');
		} finally {
			setLoading(false);
		}
	}, [navigate, getTransactions, filters.source, filters.dateFrom, filters.dateTo]);

	const applyFilters = useCallback(() => {
		let filtered = [...transactions];

		if (filters.search) {
			filtered = filtered.filter(t => 
				t.description?.toLowerCase().includes(filters.search.toLowerCase()) ||
				t.counterparty?.toLowerCase().includes(filters.search.toLowerCase())
			);
		}

		if (filters.type !== 'all') {
			filtered = filtered.filter(t => t.type === filters.type);
		}

		if (filters.source !== 'all') {
			filtered = filtered.filter(t => t.source === filters.source);
		}

		if (filters.dateFrom) {
			filtered = filtered.filter(t => 
				new Date(t.transaction_date) >= new Date(filters.dateFrom)
			);
		}

		if (filters.dateTo) {
			filtered = filtered.filter(t => 
				new Date(t.transaction_date) <= new Date(filters.dateTo)
			);
		}

		setFilteredTransactions(filtered);
	}, [transactions, filters]);

	useEffect(() => {
        fetchTransactions();
    }, [fetchTransactions]);

	useEffect(() => {
		applyFilters();
	}, [applyFilters]);

	const handleFilterChange = (e) => {
		setFilters({ ...filters, [e.target.name]: e.target.value });
	};

	const getTransactionIcon = (type) => {
		switch (type) {
			case 'income': return '💰';
			case 'expense': return '🛒';
			case 'transfer': return '💸';
			case 'trade': return '📈';
			case 'deposit': return '💵';
			case 'withdrawal': return '💸';
			default: return '💳';
		}
	};

	const getSourceIcon = (source) => {
		const icons = {
			monobank: '🏦',
			pumb: '🏛️',
			binance: '₿',
			bybit: '📊',
			okx: '🔷',
			manual: '✍️',
		};
		return icons[source] || '💼';
	};

	if (loading) {
		return (
			<>
				<Navbar />
				<div className="transactions-loading">
					<div className="spinner"></div>
					<p>Завантаження транзакцій...</p>
				</div>
			</>
		);
	}

	return (
		<>
			<Navbar />
			<div className="transactions-page">
				<div className="transactions-overlay" />

				<div className="transactions-container">
					<div className="transactions-header">
						<h1 className="transactions-title">
							<span className="title-icon">📊</span>
							Транзакції
						</h1>
					</div>

					{error && <div className="transactions-error">{error}</div>}

					<div className="transactions-filters">
						<div className="filter-group">
							<label className="filter-label">Пошук</label>
							<input
								type="text"
								name="search"
								placeholder="🔍 Пошук по опису або контрагенту"
								value={filters.search}
								onChange={handleFilterChange}
								className="filter-input filter-search"
							/>
						</div>

						<div className="filter-group">
							<label className="filter-label">Тип транзакції</label>
							<select
								name="type"
								value={filters.type}
								onChange={handleFilterChange}
								className="filter-select"
							>
								<option value="all">Всі типи</option>
								<option value="income">Дохід</option>
								<option value="expense">Витрата</option>
								<option value="transfer">Переказ</option>
								<option value="trade">Торгівля</option>
							</select>
						</div>

						<div className="filter-group">
							<label className="filter-label">Джерело</label>
							<select
								name="source"
								value={filters.source}
								onChange={handleFilterChange}
								className="filter-select"
							>
								<option value="all">Всі джерела</option>
								<option value="monobank">Monobank</option>
								<option value="pumb">ПУМБ</option>
								<option value="binance">Binance</option>
								<option value="bybit">Bybit</option>
								<option value="manual">Вручну</option>
							</select>
						</div>

						<div className="filter-group">
							<label className="filter-label">Дата від</label>
							<input
								type="date"
								name="dateFrom"
								value={filters.dateFrom}
								onChange={handleFilterChange}
								className="filter-input filter-date"
							/>
						</div>

						<div className="filter-group">
							<label className="filter-label">Дата до</label>
							<input
								type="date"
								name="dateTo"
								value={filters.dateTo}
								onChange={handleFilterChange}
								className="filter-input filter-date"
							/>
						</div>
					</div>

					<div className="transactions-list">
						{filteredTransactions.length === 0 ? (
							<div className="transactions-empty">
								<span className="empty-icon">📭</span>
								<p>Транзакцій не знайдено</p>
								<p className="empty-hint">
									{transactions.length === 0 
										? 'Додайте банк в налаштуваннях профілю для автоматичної синхронізації транзакцій'
										: 'Спробуйте змінити фільтри пошуку'}
								</p>
							</div>
						) : (
							filteredTransactions.map(transaction => {
								const isTransfer = transaction.type === 'transfer';
								const sign = transaction.type === 'income' ? '+' : (isTransfer ? '↔' : '−');
								const amountClass = transaction.type === 'income'
									? 'amount-positive'
									: isTransfer ? 'amount-neutral' : 'amount-negative';
								const d = transaction.transaction_date;
								const parsedDate = d ? new Date(d) : null;
								const dateStr = parsedDate && !isNaN(parsedDate)
									? parsedDate.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
									: '—';

								return (
									<div key={transaction.id} className={`transaction-card transaction-${transaction.type}`}>
										<div className="transaction-icon">
											{getTransactionIcon(transaction.type)}
										</div>
										<div className="transaction-details">
											<div className="transaction-main">
												<h3 className="transaction-description">{transaction.description || '—'}</h3>
												<span className={`transaction-amount ${amountClass}`}>
													{sign}{Math.abs(transaction.amount || 0).toLocaleString('uk-UA')} {transaction.currency || '₴'}
												</span>
											</div>
											<div className="transaction-meta">
												<span className="transaction-source">
													{getSourceIcon(transaction.source)} {transaction.source}
												</span>
												{transaction.counterparty && (
													<span className="transaction-counterparty">
														→ {transaction.counterparty}
													</span>
												)}
												<span className="transaction-date">{dateStr}</span>
											</div>
										</div>
									</div>
								);
							})
						)}
					</div>
				</div>
			</div>
		</>
	);
}

export default Transactions;
