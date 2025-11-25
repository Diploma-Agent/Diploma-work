import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/profileStyles.css';
import { authService } from '../api/authService';
import Navbar from '../components/Navbar';
import { financeService } from '../api/financeService';

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
	const [tokens, setTokens] = useState([]);
	const [showAddBank, setShowAddBank] = useState(false);
	const [showAddToken, setShowAddToken] = useState(false);
	const [bankForm, setBankForm] = useState({ name: '', type: 'monobank', apiKey: '' });
	const [tokenForm, setTokenForm] = useState({ 
		exchange: 'binance', 
		apiKey: '', 
		apiSecret: '', 
		name: '' 
	});
	const navigate = useNavigate();

	useEffect(() => {
		fetchUserData();
		loadBanks();
		loadTokens();
	}, []);

	const fetchUserData = async () => {
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
	};

	const loadBanks = async () => {
		try {
			const token = localStorage.getItem('token');
			const data = await financeService.getBanks(token);
			setBanks(data);
		} catch (err) {
			console.error('Помилка завантаження банків:', err);
		}
	};

	const loadTokens = async () => {
		try {
			const token = localStorage.getItem('token');
			const data = await financeService.getExchanges(token);
			setTokens(data);
		} catch (err) {
			console.error('Помилка завантаження бірж:', err);
		}
	};

	const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

	const onBankChange = (e) => setBankForm({ ...bankForm, [e.target.name]: e.target.value });

	const onTokenChange = (e) => setTokenForm({ ...tokenForm, [e.target.name]: e.target.value });

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
			const token = localStorage.getItem('token');
			await financeService.addBank(token, bankForm);
			
			setBankForm({ name: '', type: 'monobank', apiKey: '' });
			setShowAddBank(false);
			setSuccess('Банк успішно додано!');
			loadBanks();
			setTimeout(() => setSuccess(''), 3000);
		} catch (err) {
			setError(err.message);
		}
	};

	const handleRemoveBank = async (id) => {
		try {
			const token = localStorage.getItem('token');
			await financeService.deleteBank(token, id);
			setSuccess('Банк видалено!');
			loadBanks();
			setTimeout(() => setSuccess(''), 3000);
		} catch (err) {
			setError(err.message);
		}
	};

	const handleAddToken = async (e) => {
		e.preventDefault();
		if (!tokenForm.name || !tokenForm.apiKey || !tokenForm.apiSecret) {
			setError('Заповніть всі поля токена.');
			return;
		}

		try {
			const token = localStorage.getItem('token');
			await financeService.addExchange(token, tokenForm);
			
			setTokenForm({ exchange: 'binance', apiKey: '', apiSecret: '', name: '' });
			setShowAddToken(false);
			setSuccess('Токен біржі успішно додано!');
			loadTokens();
			setTimeout(() => setSuccess(''), 3000);
		} catch (err) {
			setError(err.message);
		}
	};

	const handleRemoveToken = async (id) => {
		try {
			const token = localStorage.getItem('token');
			await financeService.deleteExchange(token, id);
			setSuccess('Токен видалено!');
			loadTokens();
			setTimeout(() => setSuccess(''), 3000);
		} catch (err) {
			setError(err.message);
		}
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
				navigate('/dashboard');
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

	const renderProfileTab = () => (
		<>
			<div className="profile-header">
				<div className="profile-avatar">
					{user.first_name?.charAt(0).toUpperCase() || user.username?.charAt(0).toUpperCase() || 'U'}
				</div>
				<h2 className="profile-name">{user.first_name || user.username}</h2>
				<p className="profile-email">{user.email}</p>
			</div>

			{editMode ? (
				<form onSubmit={onSubmit} className="profile-form">
					<label className="profile-label">
						<span>Ім'я *</span>
						<input
							className="profile-input"
							name="name"
							type="text"
							placeholder="Ваше ім'я"
							value={form.name}
							onChange={onChange}
							required
						/>
					</label>

					<label className="profile-label">
						<span>Email *</span>
						<input
							className="profile-input"
							name="email"
							type="email"
							placeholder="you@example.com"
							value={form.email}
							onChange={onChange}
							required
						/>
					</label>

					<label className="profile-label">
						<span>Телефон</span>
						<input
							className="profile-input profile-input--phone"
							name="phone"
							type="tel"
							placeholder="+380 (XX) XXX-XX-XX"
							value={form.phone}
							onChange={onChange}
						/>
					</label>

					<label className="profile-label">
						<span>Дата народження</span>
						<input
							className="profile-input"
							name="dateOfBirth"
							type="date"
							value={form.dateOfBirth}
							onChange={onChange}
						/>
					</label>

					<label className="profile-label">
						<span>Місцезнаходження</span>
						<input
							className="profile-input profile-input--location"
							name="location"
							type="text"
							placeholder="Київ, Україна"
							value={form.location}
							onChange={onChange}
						/>
					</label>

					<label className="profile-label">
						<span>Біографія</span>
						<textarea
							className="profile-input profile-textarea"
							name="bio"
							placeholder="Розкажіть про себе..."
							value={form.bio}
							onChange={onChange}
							maxLength={500}
						/>
						<span className={`char-counter ${form.bio.length > 450 ? 'warning' : ''} ${form.bio.length >= 500 ? 'error' : ''}`}>
							{form.bio.length}/500
						</span>
					</label>

					<hr className="profile-section-divider" />

					<h4 className="profile-subsection-title">Соціальні мережі</h4>

					<div className="social-links-group">
						<label className="profile-label">
							<span>Telegram</span>
							<input
								className="profile-input profile-input--telegram"
								name="telegram"
								type="text"
								placeholder="@username"
								value={form.telegram}
								onChange={onChange}
							/>
						</label>

						<label className="profile-label">
							<span>LinkedIn</span>
							<input
								className="profile-input profile-input--linkedin"
								name="linkedin"
								type="url"
								placeholder="https://linkedin.com/in/username"
								value={form.linkedin}
								onChange={onChange}
							/>
						</label>
					</div>

					<div className="profile-buttons">
						<button
							type="submit"
							disabled={loading}
							className="profile-button profile-button--save"
						>
							{loading ? 'Збереження...' : 'Зберегти'}
						</button>
						<button
							type="button"
							onClick={() => {
								setEditMode(false);
								setForm({ 
									name: user.name, 
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
							}}
							className="profile-button profile-button--cancel"
						>
							Скасувати
						</button>
					</div>
				</form>
			) : (
				<>
					<div className="profile-info-grid">
						<div className="profile-info-card">
							<span className="profile-info-label">Телефон</span>
							<div className={`profile-info-value ${!user.phone ? 'empty' : ''}`}>
								{user.phone || 'Не вказано'}
							</div>
						</div>

						<div className="profile-info-card">
							<span className="profile-info-label">Дата народження</span>
							<div className={`profile-info-value ${!user.dateOfBirth ? 'empty' : ''}`}>
								{user.dateOfBirth ? new Date(user.dateOfBirth).toLocaleDateString('uk-UA') : 'Не вказано'}
							</div>
						</div>

						<div className="profile-info-card">
							<span className="profile-info-label">Місцезнаходження</span>
							<div className={`profile-info-value ${!user.location ? 'empty' : ''}`}>
								{user.location || 'Не вказано'}
							</div>
						</div>

						{user.bio && (
							<div className="profile-info-card" style={{ gridColumn: '1 / -1' }}>
								<span className="profile-info-label">Про себе</span>
								<div className="profile-info-value">{user.bio}</div>
							</div>
						)}

						{(user.telegram || user.linkedin) && (
							<>
								<div className="profile-info-card">
									<span className="profile-info-label">Telegram</span>
									<div className={`profile-info-value ${!user.telegram ? 'empty' : ''}`}>
										{user.telegram || 'Не вказано'}
									</div>
								</div>

								<div className="profile-info-card">
									<span className="profile-info-label">LinkedIn</span>
									<div className={`profile-info-value ${!user.linkedin ? 'empty' : ''}`}>
										{user.linkedin ? (
											<a href={user.linkedin} target="_blank" rel="noopener noreferrer" style={{ color: '#667eea' }}>
												Профіль
											</a>
										) : 'Не вказано'}
									</div>
								</div>
							</>
						)}
					</div>

					<div className="profile-actions">
						<button
							onClick={() => setEditMode(true)}
							className="profile-button profile-button--edit"
						>
							Редагувати профіль
						</button>
						<button
							onClick={handleLogout}
							className="profile-button profile-button--logout"
						>
							Вийти
						</button>
					</div>
				</>
			)}

			<div className="profile-info">
				<p className="profile-info-item">
					<strong>Дата реєстрації:</strong>{' '}
					{new Date(user.createdAt || Date.now()).toLocaleDateString('uk-UA')}
				</p>
			</div>
		</>
	);

	const renderBanksTab = () => {
		// Використовуємо файли з папки public/images
		const bankLogos = {
			monobank: '/images/monobank.png',
			pumb: '/images/pumb.png'
		};

		const getBankIcon = (bankType) => {
			const logo = bankLogos[bankType];
			if (!logo) {
				return <span style={{ fontSize: '32px' }}>🏦</span>;
			}
			
			return (
				<img 
					src={logo} 
					alt={bankType} 
					className="bank-logo"
					onError={(e) => {
						console.error('Помилка завантаження логотипу банку:', bankType, 'Шлях:', logo);
						e.target.onerror = null;
						e.target.style.display = 'none';
						const parent = e.target.parentElement;
						parent.innerHTML = '<span style="font-size: 32px">🏦</span>';
					}}
				/>
			);
		};

		return (
			<div className="banks-section">
				<div className="section-header">
					<h3 className="section-title">Підключені банки</h3>
					<button
						onClick={() => setShowAddBank(!showAddBank)}
						className="add-button"
					>
						{showAddBank ? '✕ Скасувати' : '+ Додати банк'}
					</button>
				</div>

				{showAddBank && (
					<form onSubmit={handleAddBank} className="add-form">
						<label className="profile-label">
							<span>Назва банку</span>
							<input
								className="profile-input"
								name="name"
								type="text"
								placeholder="Наприклад: Мій ПУМБ"
								value={bankForm.name}
								onChange={onBankChange}
								required
							/>
						</label>

						<label className="profile-label">
							<span>Тип банку</span>
							<select
								className="profile-input"
								name="type"
								value={bankForm.type}
								onChange={onBankChange}
							>
								<option value="monobank">Monobank</option>
								<option value="pumb">ПУМБ</option>
							</select>
						</label>

						<label className="profile-label">
							<span>API ключ</span>
							<input
								className="profile-input"
								name="apiKey"
								type="password"
								placeholder="Введіть API ключ банку"
								value={bankForm.apiKey}
								onChange={onBankChange}
								required
							/>
						</label>

						<button type="submit" className="profile-button profile-button--save">
							Додати банк
						</button>
					</form>
				)}

				<div className="items-list">
					{banks.length === 0 ? (
						<div className="empty-state">
							<span className="empty-icon">🏦</span>
							<p>Ще немає підключених банків</p>
							<p className="empty-hint">Додайте банк для автоматичної синхронізації транзакцій</p>
						</div>
					) : (
						banks.map(bank => (
							<div key={bank.id} className="item-card">
								<div className="item-icon">
									{getBankIcon(bank.bank_type)}
								</div>
								<div className="item-info">
									<h4 className="item-name">{bank.name}</h4>
									<p className="item-detail">{bank.bank_type?.toUpperCase()}</p>
									<p className="item-date">
										Додано: {new Date(bank.created_at).toLocaleDateString('uk-UA')}
									</p>
									<span className={`item-status ${bank.status}`}>
										{bank.status === 'active' ? '● Активний' : '○ Неактивний'}
									</span>
								</div>
								<button
									onClick={() => handleRemoveBank(bank.id)}
									className="remove-button"
									title="Видалити"
								>
									🗑️
								</button>
							</div>
						))
					)}
				</div>
			</div>
		);
	};

	const renderTokensTab = () => {
		// Використовуємо файли з папки public/images
		const exchangeLogos = {
			binance: '/images/binance.png',
			bybit: '/images/bybit.png',
			okx: '/images/okx.png'
		};

		const getExchangeIcon = (exchange) => {
			const logo = exchangeLogos[exchange];
			if (!logo) {
				return <span style={{ fontSize: '32px' }}>📊</span>;
			}
			
			return (
				<img 
					src={logo} 
					alt={exchange} 
					className="exchange-logo"
					onError={(e) => {
						console.error('Помилка завантаження логотипу біржі:', exchange, 'Шлях:', logo);
						e.target.onerror = null;
						e.target.style.display = 'none';
						const parent = e.target.parentElement;
						parent.innerHTML = '<span style="font-size: 32px">📊</span>';
					}}
				/>
			);
		};

		return (
			<div className="tokens-section">
				<div className="section-header">
					<h3 className="section-title">Токени бірж</h3>
					<button
						onClick={() => setShowAddToken(!showAddToken)}
						className="add-button"
					>
						{showAddToken ? '✕ Скасувати' : '+ Додати біржу'}
					</button>
				</div>

				{showAddToken && (
					<form onSubmit={handleAddToken} className="add-form">
						<label className="profile-label">
							<span>Назва підключення</span>
							<input
								className="profile-input"
								name="name"
								type="text"
								placeholder="Наприклад: Мій Binance"
								value={tokenForm.name}
								onChange={onTokenChange}
								required
							/>
						</label>

						<label className="profile-label">
							<span>Біржа</span>
							<select
								className="profile-input"
								name="exchange"
								value={tokenForm.exchange}
								onChange={onTokenChange}
							>
								<option value="binance">Binance</option>
								<option value="bybit">Bybit</option>
								<option value="okx">OKX</option>
							</select>
						</label>

						<label className="profile-label">
							<span>API Key</span>
							<input
								className="profile-input"
								name="apiKey"
								type="text"
								placeholder="Введіть API ключ біржі"
								value={tokenForm.apiKey}
								onChange={onTokenChange}
								required
							/>
						</label>

						<label className="profile-label">
							<span>API Secret</span>
							<input
								className="profile-input"
								name="apiSecret"
								type="password"
								placeholder="Введіть секретний ключ"
								value={tokenForm.apiSecret}
								onChange={onTokenChange}
								required
							/>
							<small className="input-hint">
								⚠️ Ключі зберігаються локально та не передаються на сервер
							</small>
						</label>

						<button type="submit" className="profile-button profile-button--save">
							Додати біржу
						</button>
					</form>
				)}

				<div className="items-list">
					{tokens.length === 0 ? (
						<div className="empty-state">
							<span className="empty-icon">📊</span>
							<p>Ще немає підключених бірж</p>
							<p className="empty-hint">Додайте API ключі для автоматичної синхронізації балансу</p>
						</div>
					) : (
						tokens.map(token => (
							<div key={token.id} className="item-card">
								<div className="item-icon">
									{getExchangeIcon(token.exchange)}
								</div>
								<div className="item-info">
									<h4 className="item-name">{token.name}</h4>
									<p className="item-detail">{token.exchange?.toUpperCase()}</p>
									<p className="item-detail token-value">
										API Key: {token.api_key_masked || 'Захищено'}
									</p>
									<p className="item-date">
										Додано: {new Date(token.created_at).toLocaleDateString('uk-UA')}
									</p>
									<span className={`item-status ${token.status}`}>
										{token.status === 'active' ? '● Активний' : '○ Неактивний'}
									</span>
								</div>
								<button
									onClick={() => handleRemoveToken(token.id)}
									className="remove-button"
									title="Видалити"
								>
									🗑️
								</button>
							</div>
						))
					)}
				</div>
			</div>
		);
	};

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
							{activeTab === 'profile' && renderProfileTab()}
							{activeTab === 'banks' && renderBanksTab()}
							{activeTab === 'tokens' && renderTokensTab()}
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
