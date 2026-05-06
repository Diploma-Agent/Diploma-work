// В dev — Vite proxy перенаправляє /api/* → localhost:8000
// В production — VITE_API_BASE_URL вказує на Render backend URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const API_URL = `${API_BASE}/api/auth`;

export const authService = {
	async register(data) {
		const response = await fetch(`${API_URL}/register/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				email: data.email,
				password: data.password,
				username: data.email 
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.message || 'Помилка реєстрації');
		}

		return response.json();
	},

	async login(data) {
		const response = await fetch(`${API_URL}/login/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				email: data.email,
				password: data.password
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.email || error.password || 'Невірний email або пароль');
		}

		const result = await response.json();
		
		// Зберігаємо access і refresh токени
		if (result.access) {
			localStorage.setItem('token', result.access);
			localStorage.setItem('refreshToken', result.refresh);
		}

		return { token: result.access, ...result };
	},

	async getMe(token) {
		const response = await fetch(`${API_URL}/profile/`, {
			method: 'GET',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
		});

		if (!response.ok) {
			// Якщо токен невалідний, спробуємо оновити його
			if (response.status === 401) {
				const refreshToken = localStorage.getItem('refreshToken');
				if (refreshToken) {
					try {
						const newToken = await this.refreshToken(refreshToken);
						// Повторюємо запит з новим токеном
						return this.getMe(newToken);
					} catch {
						throw new Error('Сесія закінчилась. Увійдіть знову.');
					}
				}
			}
			throw new Error('Помилка отримання даних користувача');
		}

		return response.json();
	},

	async refreshToken(refreshToken) {
		const response = await fetch(`${API_URL}/token/refresh/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ refresh: refreshToken }),
		});

		if (!response.ok) {
			throw new Error('Не вдалось оновити токен');
		}

		const result = await response.json();
		
		if (result.access) {
			localStorage.setItem('token', result.access);
		}

		return result.access;
	},

	async updateProfile(token, data) {
		const response = await fetch(`${API_URL}/profile/`, {
			method: 'PATCH',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				first_name: data.name,
				email: data.email,
				phone: data.phone || '',
				dateOfBirth: data.dateOfBirth || null,
				location: data.location || '',
				bio: data.bio || '',
				telegram: data.telegram || '',
				linkedin: data.linkedin || ''
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.message || 'Помилка оновлення профілю');
		}

		return response.json();
	},
};
