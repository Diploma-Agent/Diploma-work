import api from './axios';

// Auth Service для роботи з Django backend
export const authService = {
	// Реєстрація користувача
	register: async (userData) => {
		try {
			// Backend очікує username, password, password2, email
			const response = await api.post('/api/auth/register/', {
				username: userData.email.split('@')[0], // Використовуємо частину email як username
				email: userData.email,
				password: userData.password,
				password2: userData.password,
				first_name: userData.name || '',
			});
			return response.data;
		} catch (error) {
			throw new Error(
				error.response?.data?.error || 
				error.response?.data?.message || 
				error.response?.data?.username?.[0] ||
				error.response?.data?.email?.[0] ||
				'Помилка реєстрації'
			);
		}
	},

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
				}
			}
			
			return {
				token: response.data.access,
				user: response.data.user,
			};
		} catch (error) {
			throw new Error(
				error.response?.data?.error || 
				error.response?.data?.message || 
				'Невірний email або пароль'
			);
		}
	},

	// Отримання даних поточного користувача
	getMe: async () => {
		try {
			const response = await api.get('/api/auth/profile/');
			return response.data;
		} catch (error) {
			throw new Error(
				error.response?.data?.error || 
				'Помилка отримання даних користувача'
			);
		}
	},

	// Оновлення профілю
	updateProfile: async (profileData) => {
		try {
			const response = await api.put('/api/auth/profile/', profileData);
			return response.data;
		} catch (error) {
			throw new Error(
				error.response?.data?.error || 
				'Помилка оновлення профілю'
			);
		}
	},

	// Вихід (очищення токенів)
	logout: () => {
		localStorage.removeItem('token');
		localStorage.removeItem('refreshToken');
	},
};
