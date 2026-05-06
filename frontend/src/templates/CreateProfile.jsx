import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/authStyles.css';

function CreateProfile() {
	const [form, setForm] = useState({
		avatar: '',
		phone: '',
		bio: '',
		preferences: {
			currency: 'UAH',
			language: 'uk',
			notifications: true
		}
	});
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(false);
	const navigate = useNavigate();

	const onChange = (e) => {
		const { name, value, type, checked } = e.target;
		
		if (name.startsWith('preferences.')) {
			const prefKey = name.split('.')[1];
			setForm({
				...form,
				preferences: {
					...form.preferences,
					[prefKey]: type === 'checkbox' ? checked : value
				}
			});
		} else {
			setForm({ ...form, [name]: type === 'checkbox' ? checked : value });
		}
	};

	const onSubmit = async (e) => {
		e.preventDefault();
		setError('');

		try {
			setLoading(true);
			navigate('/profile');
		} catch (err) {
			setError(err.message || 'Сталася помилка.');
		} finally {
			setLoading(false);
		}
	};

	const skipSetup = () => {
		navigate('/profile');
	};

	return (
		<div className="auth-page-wrapper">
			<div className="auth-overlay" />
			
			<div className="auth-particles">
				<div className="auth-particle"></div>
				<div className="auth-particle"></div>
				<div className="auth-particle"></div>
			</div>

			<div className="auth-rings">
				<div className="auth-ring"></div>
				<div className="auth-ring"></div>
			</div>

			<div className="auth-container">
				<div className="auth-form-card" style={{ maxWidth: '600px' }}>
					<h2 className="auth-title">Налаштування профілю</h2>
					<p style={{ textAlign: 'center', color: '#718096', marginBottom: '20px' }}>
						Заповніть додаткову інформацію про себе
					</p>
					
					{error && <div className="auth-error">{error}</div>}
					
					<form onSubmit={onSubmit} noValidate>
						<label className="auth-label">
							Номер телефону (необов'язково)
							<input
								className="auth-input"
								name="phone"
								type="tel"
								placeholder="+380 XX XXX XX XX"
								value={form.phone}
								onChange={onChange}
							/>
						</label>

						<label className="auth-label">
							Про себе (необов'язково)
							<textarea
								className="auth-input"
								name="bio"
								placeholder="Розкажіть трохи про себе..."
								value={form.bio}
								onChange={onChange}
								rows={3}
								style={{ resize: 'vertical', fontFamily: 'inherit' }}
							/>
						</label>

						<label className="auth-label">
							Валюта за замовчуванням
							<select
								className="auth-input"
								name="preferences.currency"
								value={form.preferences.currency}
								onChange={onChange}
							>
								<option value="UAH">Гривня (₴)</option>
								<option value="USD">Долар ($)</option>
								<option value="EUR">Євро (€)</option>
							</select>
						</label>

						<label className="auth-label">
							Мова інтерфейсу
							<select
								className="auth-input"
								name="preferences.language"
								value={form.preferences.language}
								onChange={onChange}
							>
								<option value="uk">Українська</option>
								<option value="en">English</option>
							</select>
						</label>

						<label className="auth-label" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
							<input
								type="checkbox"
								name="preferences.notifications"
								checked={form.preferences.notifications}
								onChange={onChange}
								style={{ width: 'auto', margin: 0 }}
							/>
							<span>Отримувати сповіщення</span>
						</label>

						<button type="submit" disabled={loading} className="auth-button">
							{loading ? 'Збереження...' : 'Зберегти та продовжити'}
						</button>

						<button
							type="button"
							onClick={skipSetup}
							className="auth-button"
							style={{
								background: 'transparent',
								color: '#667eea',
								border: '2px solid #667eea',
								marginTop: '10px'
							}}
						>
							Пропустити
						</button>
					</form>
				</div>
			</div>
		</div>
	);
}

export default CreateProfile;
