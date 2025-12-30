const API_URL = 'http://localhost:8000/api/finance';

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

	// === АНАЛІТИКА БАНКУ ===
	async getBankAnalytics(token) {
		const response = await fetch(`${API_URL}/analytics/bank/`, {
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
		const response = await fetch(`${API_URL}/exchanges/add/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				exchange_name: data.exchange,
				api_key: data.apiKey,
				api_secret: data.apiSecret,
			}),
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
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка отримання балансу біржі');
		return response.json();
	},

	async getExchangeOrders(token, exchange, category = 'spot', symbol = '', settleCoin = '') {
		let url = `${API_URL}/exchanges/orders/?exchange=${exchange}&category=${category}`;
		if (symbol) url += `&symbol=${symbol}`;
		if (settleCoin) url += `&settleCoin=${settleCoin}`;

		const response = await fetch(url, {
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка отримання ордерів');
		return response.json();
	},

	// === ТРАНЗАКЦІЇ ===
	async getTransactions(token, source = 'all', days = 30) {
		const response = await fetch(`${API_URL}/transactions/?source=${source}&days=${days}`, {
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка отримання транзакцій');
		return response.json();
	},
};
