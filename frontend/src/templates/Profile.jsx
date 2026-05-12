import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/profileStyles.css';
import { authService } from '../api/authService';
import Navbar from '../components/Navbar';
import { financeService } from '../api/financeService';

// Import sub-components
import ProfileTab from '../components/profile/ProfileTab';
import BanksTab from '../components/profile/BanksTab';
import TokensTab from '../components/profile/TokensTab';

function Profile() {
	const [user, setUser] = useState(null);
	const [editMode, setEditMode] = useState(false);
	const [form, setForm] = useState({ 
		name: '', 
		email: '', 
		phone: '', 
		bio: '', 
		dateOfBirth: '', 
		location: '',
		telegram: '',
		linkedin: ''
	});
	const [error, setError] = useState('');
	const [success, setSuccess] = useState('');
	const [loading, setLoading] = useState(false);
	const [activeTab, setActiveTab] = useState('profile'); // profile, banks, tokens
	const [banks, setBanks] = useState([]);
	const [showAddBank, setShowAddBank] = useState(false);
	const [bankForm, setBankForm] = useState({ name: '', type: 'monobank', apiKey: '' });
	const [syncingBankId, setSyncingBankId] = useState(null);
	const [addingBank, setAddingBank] = useState(false);
	const [addingBankProgress, setAddingBankProgress] = useState(null); // 'validating' (перевірка токену та додавання) -> 'syncing' (завантаження транзакцій у фоні)
	const [removingBankId, setRemovingBankId] = useState(null);
	const navigate = useNavigate();

	const fetchUserData = useCallback(async () => {
		try {
			const token = localStorage.getItem('token');
			if (!token) {
				navigate('/login');
				return;
			}

			const data = await authService.getMe(token);
			setUser(data);
			setForm({ 
				name: data.first_name || data.username, 
				email: data.email,
				phone: data.phone || '',
				bio: data.bio || '',
				dateOfBirth: data.dateOfBirth || '',
				location: data.location || '',
				telegram: data.telegram || '',
				linkedin: data.linkedin || ''
			});
		} catch (err) {
			console.error('Помилка завантаження профілю:', err);
			setError(err.message);
			
			// Не видаляємо токен одразу, показуємо помилку
			// Якщо помилка про сесію - тоді перенаправляємо
			if (err.message.includes('Сесія закінчилась')) {
				localStorage.removeItem('token');
				localStorage.removeItem('refreshToken');
				setTimeout(() => navigate('/login'), 2000);
			}
		}
	}, [navigate]);

	const loadBanks = useCallback(async () => {
		try {
			const token = localStorage.getItem('token');
			const data = await financeService.getBanks(token);
			setBanks(data);
		} catch (err) {
			console.error('Помилка завантаження банків:', err);
		}
	}, []);

	useEffect(() => {
		fetchUserData();
		loadBanks();
	}, [fetchUserData, loadBanks]);

	const onChange = (e) => {
		const { name, value } = e.target;
		
		if (name === 'phone') {
			let digits = value.replace(/\D/g, '');
			if (digits.length > 12) {
				digits = digits.slice(0, 12);
			}
			
			let formatted = '';
			if (digits.length > 0) {
				formatted = '+';
				formatted += digits.substring(0, 3);
			}
			if (digits.length > 3) {
				formatted += ' (' + digits.substring(3, 5);
			}
			if (digits.length > 5) {
				formatted += ') ' + digits.substring(5, 8);
			}
			if (digits.length > 8) {
				formatted += '-' + digits.substring(8, 10);
			}
			if (digits.length > 10) {
				formatted += '-' + digits.substring(10, 12);
			}
			
			if (digits.length === 0) formatted = '';

			setForm({ ...form, [name]: formatted });
			return;
		}

		setForm({ ...form, [name]: value });
	};

	const onBankChange = (e) => setBankForm({ ...bankForm, [e.target.name]: e.target.value });

	const onSubmit = async (e) => {
		e.preventDefault();
		setError('');
		setSuccess('');

		if (!form.name || !form.email) {
			setError('Заповніть всі поля.');
			return;
		}

		try {
			setLoading(true);
			const token = localStorage.getItem('token');
			const data = await authService.updateProfile(token, form);
			
			setUser(data);
			setSuccess('Профіль успішно оновлено!');
			setEditMode(false);
		} catch (err) {
			setError(err.message || 'Сталася помилка.');
		} finally {
			setLoading(false);
		}
	};

	const handleAddBank = async (e) => {
		e.preventDefault();
		if (!bankForm.name || !bankForm.apiKey) {
			setError('Заповніть всі поля банку.');
			return;
		}

		try {
			setAddingBank(true);
			setAddingBankProgress('validating_token');
			setError('');
			const token = localStorage.getItem('token');

			// 1. Спочатку робимо запит до нашого бекенду для валідації та збереження
			const newBank = await financeService.addBank(token, bankForm);

			setAddingBankProgress('saving');
			setTimeout(() => setAddingBankProgress('syncing'), 600); // small delay for UI smoothness
			
			// 2. Синхронізуємо транзакції за поточний місяць
			const today = new Date();
			
			// Форматуємо дати безпечно з урахуванням локальної зони (YYYY-MM-DD)
			const getLocalDateString = (date) => {
				const y = date.getFullYear();
				const m = String(date.getMonth() + 1).padStart(2, '0');
				const d = String(date.getDate()).padStart(2, '0');
				return `${y}-${m}-${d}`;
			};

			const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
			const dateFrom = getLocalDateString(firstDayOfMonth);
			const dateTo = getLocalDateString(today);

			await financeService.syncTransactions(
                token, 
                bankForm.type, 
                null, 
                dateFrom, 
                dateTo, 
                newBank.id 
            );

			setAddingBankProgress('redirecting');
			setSuccess('Банк успішно додано!');
			setBankForm({ name: '', type: 'monobank', apiKey: '' });
			setShowAddBank(false);

			// 3. Завершуємо додавання банку
			setTimeout(() => {
				setAddingBankProgress(null);
				setAddingBank(false);
				loadBanks();
			}, 1000);
			
		} catch (err) {
			setError(err.message);
			setAddingBankProgress(null);
			setAddingBank(false);
		}
	};

	const handleRemoveBank = async (id) => {
		try {
			setRemovingBankId(id);
			const token = localStorage.getItem('token');
			await financeService.deleteBank(token, id);
			// Миттєво видаляємо банк з локального списку для швидкого відображення
			setBanks(prev => prev.filter(b => b.id !== id));
			setSuccess('Банк видалено!');
			// Все одно викликаємо loadBanks для гарантованої синхронізації з сервером
			loadBanks();
			setTimeout(() => setSuccess(''), 3000);
		} catch (err) {
			setError(err.message);
		} finally {
			setRemovingBankId(null);
		}
	};

	const handleSyncBank = async (bank) => {
		try {
			setSyncingBankId(bank.id);
			setError('');
			const token = localStorage.getItem('token');
			const result = await financeService.syncTransactions(token, bank.bank_name, 30, null, null, bank.id);
			setSuccess(`Синхронізовано: +${result.transactions_added} нових, оновлено ${result.transactions_updated}`);
			setTimeout(() => setSuccess(''), 5000);
		} catch (err) {
			setError(err.message || 'Помилка синхронізації');
		} finally {
			setSyncingBankId(null);
		}
	};

	const handleCancelEdit = () => {
		setEditMode(false);
		setForm({ 
			name: user.first_name || user.username, 
			email: user.email,
			phone: user.phone || '',
			bio: user.bio || '',
			dateOfBirth: user.dateOfBirth || '',
			location: user.location || '',
			telegram: user.telegram || '',
			linkedin: user.linkedin || ''
		});
		setError('');
		setSuccess('');
	};

	const handleLogout = () => {
		localStorage.removeItem('token');
		navigate('/login');
	};

	const handleFinishSetup = async () => {
		setError('');
		setSuccess('');

		try {
			// Якщо в режимі редагування, спочатку зберігаємо дані
			if (editMode) {
				if (!form.name || !form.email) {
					setError('Заповніть обов\'язкові поля (Ім\'я та Email) перед завершенням.');
					return;
				}

				setLoading(true);
				const token = localStorage.getItem('token');
				await authService.updateProfile(token, form);
			}

			// Позначаємо, що налаштування завершено
			localStorage.setItem('setupCompleted', 'true');
			
			// Показуємо повідомлення про успіх
			setSuccess('Налаштування завершено! Перенаправлення...');
			
			// Перенаправляємо на головну через 1 секунду
			setTimeout(() => {
				navigate('/');
			}, 1000);
		} catch (err) {
			setError(err.message || 'Помилка при збереженні даних.');
		} finally {
			setLoading(false);
		}
	};

	if (!user) {
		return (
			<div className="profile-loading">
				<div className="spinner"></div>
				<p>Завантаження...</p>
			</div>
		);
	}

	return (
		<>
			<Navbar />
			<div className="profile-page-wrapper">
				<div className="profile-overlay" />
				
				<div className="profile-particles">
					<div className="profile-particle"></div>
					<div className="profile-particle"></div>
					<div className="profile-particle"></div>
				</div>

				<div className="profile-container profile-container--extended">
					<div className="profile-card">
						{error && <div className="profile-error">{error}</div>}
						{success && <div className="profile-success">{success}</div>}

						<div className="profile-tabs">
							<button
								className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
								onClick={() => setActiveTab('profile')}
							>
								👤 Профіль
							</button>
							<button
								className={`tab-button ${activeTab === 'banks' ? 'active' : ''}`}
								onClick={() => setActiveTab('banks')}
							>
								🏦 Банки
							</button>
							<button
								className={`tab-button ${activeTab === 'tokens' ? 'active' : ''}`}
								onClick={() => setActiveTab('tokens')}
							>
								🔑 Токени
							</button>
						</div>

						<div className="tab-content">
							{activeTab === 'profile' && (
								<ProfileTab 
									user={user}
									editMode={editMode}
									setEditMode={setEditMode}
									form={form}
									onChange={onChange}
									onSubmit={onSubmit}
									handleLogout={handleLogout}
									onCancelEdit={handleCancelEdit}
									loading={loading}
								/>
							)}
							
							{activeTab === 'banks' && (
								<BanksTab
									banks={banks}
									showAddBank={showAddBank}
									setShowAddBank={setShowAddBank}
									bankForm={bankForm}
									onBankChange={onBankChange}
									handleAddBank={handleAddBank}
									handleRemoveBank={handleRemoveBank}
									handleSyncBank={handleSyncBank}
									syncingBankId={syncingBankId}
									addingBank={addingBank}
									addingBankProgress={addingBankProgress}
									removingBankId={removingBankId}
								/>
							)}
							
							{activeTab === 'tokens' && (
								<TokensTab />
							)}
						</div>

						{/* Кнопка завершити налаштування */}
						<div className="finish-setup-section">
							<button
								onClick={handleFinishSetup}
								className="profile-button profile-button--finish"
								disabled={loading}
							>
								{loading ? '⏳ Збереження...' : '✅ Завершити налаштування'}
							</button>
							<p className="setup-hint">
								{editMode 
									? '💡 Дані профілю будуть збережені автоматично' 
									: '💡 Натисніть, щоб перейти до головної сторінки'
								}
							</p>
						</div>
					</div>
				</div>
			</div>
		</>
	);
}

export default Profile;
