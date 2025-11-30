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
		const response = await fetch(`${API_URL}/banks/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				name: data.name,
				bank_type: data.type,
				api_key: data.apiKey,
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.detail || 'Помилка додавання банку');
		}
		return response.json();
	},

	async deleteBank(token, id) {
		const response = await fetch(`${API_URL}/banks/${id}/`, {
			method: 'DELETE',
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка видалення банку');
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
		const response = await fetch(`${API_URL}/exchanges/`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				name: data.name,
				exchange: data.exchange,
				api_key: data.apiKey,
				api_secret: data.apiSecret,
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.detail || 'Помилка додавання біржі');
		}
		return response.json();
	},

	async deleteExchange(token, id) {
		const response = await fetch(`${API_URL}/exchanges/${id}/`, {
			method: 'DELETE',
			headers: {
				'Authorization': `Bearer ${token}`,
			},
		});

		if (!response.ok) throw new Error('Помилка видалення біржі');
	},
};
