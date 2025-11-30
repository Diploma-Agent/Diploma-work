const API_URL = 'http://localhost:8000/api/auth';

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
				username: data.email  // використовуємо email як username
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.message || 'Помилка реєстрації');
		}

		return response.json();
	},

<<<<<<< HEAD
	// Вхід користувача
	login: async (credentials) => {
		try {
			// Backend підтримує як username, так і email
			const response = await api.post('/api/auth/login/', {
				username: credentials.login || credentials.email, // Можна відправляти email або username
				password: credentials.password,
			});
			
			// Зберігаємо токен
			if (response.data.access) {
				localStorage.setItem('token', response.data.access);
				if (response.data.refresh) {
					localStorage.setItem('refreshToken', response.data.refresh);
=======
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
					} catch (err) {
						throw new Error('Сесія закінчилась. Увійдіть знову.');
					}
>>>>>>> 78d8282a91de0e2d3e71f9a3f097b2ced98d3848
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
				email: data.email
			}),
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.message || 'Помилка оновлення профілю');
		}

		return response.json();
	},
};
