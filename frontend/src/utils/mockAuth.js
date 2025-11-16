// Helper function для імітації затримки мережі
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Тимчасовий токен для тестування
const mockToken = 'mock-jwt-token-12345';

// Тимчасовий користувач
let mockUser = {
	id: '1',
	name: 'Тестовий Користувач',
	email: 'test@example.com',
	createdAt: new Date().toISOString(),
	phone: '',
	bio: '',
	dateOfBirth: '',
	location: '',
	telegram: '',
	linkedin: ''
};

export const mockAuth = {
	// Реєстрація користувача
	register: async (userData) => {
		await delay(1000);
		const { name, email, password } = userData;
		
		// Отримуємо всіх користувачів з localStorage
		const users = JSON.parse(localStorage.getItem('mockUsers') || '[]');
		
		// Перевіряємо чи користувач вже існує
		const existingUser = users.find(u => u.email === email);
		if (existingUser) {
			throw new Error('Користувач з таким email вже існує');
		}
		
		// Створюємо нового користувача
		const newUser = {
			id: Date.now().toString(),
			name,
			email,
			password, // В реальному додатку пароль потрібно хешувати!
			createdAt: new Date().toISOString(),
			phone: '',
			bio: '',
			dateOfBirth: '',
			location: '',
			telegram: '',
			linkedin: ''
		};
		
		users.push(newUser);
		localStorage.setItem('mockUsers', JSON.stringify(users));
		
		return { success: true, message: 'Реєстрація успішна' };
	},

	// Вхід користувача
	login: async (credentials) => {
		await delay(800);
		const { email, password } = credentials;
		
		const users = JSON.parse(localStorage.getItem('mockUsers') || '[]');
		const user = users.find(u => u.email === email && u.password === password);
		
		if (!user) {
			throw new Error('Невірний email або пароль');
		}
		
		// Зберігаємо поточного користувача
		mockUser = { ...user };
		delete mockUser.password;
		localStorage.setItem('mockUser', JSON.stringify(mockUser));
		
		return {
			token: mockToken,
			user: mockUser
		};
	},

	// Отримання даних поточного користувача
	getMe: async (token) => {
		await delay(300);
		
		if (token !== mockToken) {
			throw new Error('Невірний токен');
		}

		// Отримуємо користувача з localStorage
		const savedUser = localStorage.getItem('mockUser');
		if (savedUser) {
			const userData = JSON.parse(savedUser);
			mockUser = { ...userData };
		}

		return { ...mockUser };
	},

	// Оновлення профілю
	updateProfile: async (token, profileData) => {
		await delay(500);
		
		if (token !== mockToken) {
			throw new Error('Невірний токен');
		}

		// Оновлюємо дані користувача
		const updatedUser = {
			...mockUser,
			...profileData,
			updatedAt: new Date().toISOString()
		};
		
		// Зберігаємо в localStorage
		localStorage.setItem('mockUser', JSON.stringify(updatedUser));
		mockUser = { ...updatedUser };

		// Також оновлюємо в списку всіх користувачів
		const users = JSON.parse(localStorage.getItem('mockUsers') || '[]');
		const userIndex = users.findIndex(u => u.id === mockUser.id);
		if (userIndex !== -1) {
			users[userIndex] = { ...updatedUser, password: users[userIndex].password };
			localStorage.setItem('mockUsers', JSON.stringify(users));
		}

		return updatedUser;
	}
};
