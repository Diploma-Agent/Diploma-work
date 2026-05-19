// В dev — Vite proxy перенаправляє /api/* → localhost:8000
// В production — VITE_API_BASE_URL вказує на Render backend URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const API_URL = `${API_BASE}/api/finance`;

export const financeService = {
	// === БАНКИ ===
	async getBanks(token) {
		const response = await fetch(`${API_URL}/banks/`, {
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка отримання банків');
		return response.json();
	},

	async addBank(token, data) {
		const response = await fetch(`${API_URL}/banks/add/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				name: data.name,  // Назва підключення
				bank_name: data.type,  // monobank або pumb
				access_token: data.apiKey,
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Помилка додавання банку');
		}
		return response.json();
	},

	async deleteBank(token, id) {
		const response = await fetch(`${API_URL}/banks/${id}/delete/`, {
			method: 'DELETE',
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка видалення банку');
	},

	async syncTransactions(token, source, days = null, dateFrom = null, dateTo = null, connectionId = null) {
		const body = { source };
		if (days) body.days = days;
		if (dateFrom) body.date_from = dateFrom;
		if (dateTo) body.date_to = dateTo;
		if (connectionId) body.connection_id = connectionId;

		const response = await fetch(`${API_URL}/transactions/sync/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body),
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({}));
			throw new Error(error.error || 'Помилка синхронізації');
		}
		return response.json();
	},

	// === АНАЛІТИКА БАНКУ ===
	async getBankAnalytics(token, connectionIds = null) {
		let url = `${API_URL}/analytics/bank/`;
		
		if (connectionIds) {
			const idParam = Array.isArray(connectionIds) ? connectionIds.join(',') : connectionIds;
			url += `?connection_id=${idParam}`;
		}

		const response = await fetch(url, {
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка отримання банківської аналітики');
		return response.json();
	},

	// === БІРЖІ ===
	async getExchanges(token) {
		const response = await fetch(`${API_URL}/exchanges/`, {
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка отримання бірж');
		return response.json();
	},

	async addExchange(token, data) {
		const body = {
			exchange_name: data.exchange,
			api_key: data.apiKey,
			api_secret: data.apiSecret,
		};
		if (data.exchange === 'okx' && data.passphrase) {
			body.api_passphrase = data.passphrase;
		}

		const response = await fetch(`${API_URL}/exchanges/add/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Помилка додавання біржі');
		}
		return response.json();
	},

	async deleteExchange(token, id) {
		const response = await fetch(`${API_URL}/exchanges/${id}/delete/`, {
			method: 'DELETE',
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка видалення біржі');
	},

	async getExchangeBalance(token, exchange) {
		const response = await fetch(`${API_URL}/exchanges/balance/?exchange=${exchange}`, {
			headers: { 'Authorization': `Bearer ${token}` },
		});
		// Завжди повертаємо JSON — бекенд повертає порожні дані при помилці API біржі
		const data = await response.json().catch(() => ({ list: [], available: false }));
		return data;
	},

	async getExchangeOrders(token, exchange, category = 'spot', symbol = '', settleCoin = '') {
		let url = `${API_URL}/exchanges/orders/?exchange=${exchange}&category=${category}`;
		if (symbol) url += `&symbol=${symbol}`;
		if (settleCoin) url += `&settleCoin=${settleCoin}`;

		const response = await fetch(url, {
			headers: { 'Authorization': `Bearer ${token}` },
		});
		// Futures можуть бути недоступні — повертаємо порожній список без throw
		const data = await response.json().catch(() => ({ list: [], available: false }));
		return data;
	},

	// === АКАУНТИ (банки + біржі разом для фільтрів) ===
	async getAccounts(token) {
		const response = await fetch(`${API_URL}/accounts/`, {
			headers: { 'Authorization': `Bearer ${token}` },
		});
		if (!response.ok) throw new Error('Помилка отримання акаунтів');
		return response.json();
	},

	// === ТРАНЗАКЦІЇ ===
	// connectionIds — масив числових ID (BankConnection.id / CryptoExchange.id)
	// sources — масив рядків ('monobank', 'binance', ...)
	async getTransactions(token, source = 'all', days = 30, dateFrom = '', dateTo = '', connectionIds = [], sources = []) {
        let url = `${API_URL}/transactions/?days=${days}`;

        if (connectionIds.length > 0) {
            url += `&connection_ids=${connectionIds.join(',')}`;
        } else if (sources.length > 0) {
            url += `&sources=${sources.join(',')}`;
        } else if (source !== 'all') {
            url += `&source=${source}`;
        }

        if (dateFrom) url += `&date_from=${dateFrom}`;
        if (dateTo) url += `&date_to=${dateTo}`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` },
        });

        if (!response.ok) throw new Error('Помилка отримання транзакцій');
        return response.json();
    },

	// === AI AGENTS ===
	async aiChat(token, message) {
		const response = await fetch(`${API_URL}/ai/chat/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ message }),
		});

		if (!response.ok) throw new Error('Помилка AI чату');
		return response.json();
	},

	async getChatHistory(token, limit = 50) {
		const response = await fetch(`${API_URL}/ai/chat/history/?limit=${limit}`, {
			headers: { 'Authorization': `Bearer ${token}` },
		});
		if (!response.ok) throw new Error('Помилка завантаження історії чату');
		return response.json();
	},

	async clearChatHistory(token) {
		const response = await fetch(`${API_URL}/ai/chat/history/`, {
			method: 'DELETE',
			headers: { 'Authorization': `Bearer ${token}` },
		});
		if (!response.ok) throw new Error('Помилка очищення історії чату');
		return response.json();
	},

	async aiAnalyst(token, question = null, connectionId = null) {
		const response = await fetch(`${API_URL}/ai/analyst/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ question, connection_id: connectionId }),
		});

		if (!response.ok) throw new Error('Помилка AI аналітика');
		return response.json();
	},

	async aiForecast(token, days = 30, connectionId = null) {
		let url = `${API_URL}/ai/forecast/?days=${days}`;
		if (connectionId) url += `&connection_id=${connectionId}`;
		const response = await fetch(url, {
			headers: { 'Authorization': `Bearer ${token}` },
		});

		if (!response.ok) throw new Error('Помилка AI прогнозу');
		return response.json();
	},

	async aiAnomaly(token, connectionId = null) {
		let url = `${API_URL}/ai/anomaly/`;
		if (connectionId) url += `?connection_id=${connectionId}`;
		const response = await fetch(url, {
			headers: { 'Authorization': `Bearer ${token}` },
		});

		if (!response.ok) throw new Error('Помилка AI аномалій');
		return response.json();
	},

	async aiInvestment(token, connectionId = null) {
		let url = `${API_URL}/ai/investment/`;
		if (connectionId) url += `?connection_id=${connectionId}`;
		const response = await fetch(url, {
			headers: { 'Authorization': `Bearer ${token}` },
		});

		if (!response.ok) throw new Error('Помилка AI інвестицій');
		return response.json();
	},
};
