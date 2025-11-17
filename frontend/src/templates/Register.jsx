import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/authStyles.css';
import { authService } from '../api/authService';

function Register() {
	const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(false);
	const navigate = useNavigate();

	const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

	const onSubmit = async (e) => {
		e.preventDefault();
		setError('');

		if (!form.name || !form.email || !form.password || !form.confirm) {
			setError('Заповніть всі поля.');
			return;
		}
		if (form.password !== form.confirm) {
			setError('Паролі не співпадають.');
			return;
		}

		try {
			setLoading(true);
			
			await authService.register({
				name: form.name,
				email: form.email,
				password: form.password,
			});
			
			// Після реєстрації автоматично логінимо користувача
			const loginData = await authService.login({
				email: form.email,
				password: form.password,
			});
			
			if (loginData.token) {
				// Токен вже збережено в authService.login
				navigate('/dashboard');
			}
		} catch (err) {
			setError(err.message || 'Сталася помилка.');
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="auth-page-wrapper">
			<div className="auth-overlay" />
			
			{/* Анімовані частинки */}
			<div className="auth-particles">
				<div className="auth-particle"></div>
				<div className="auth-particle"></div>
				<div className="auth-particle"></div>
				<div className="auth-particle"></div>
				<div className="auth-particle"></div>
				<div className="auth-particle"></div>
			</div>

			{/* Пульсуючі кільця */}
			<div className="auth-rings">
				<div className="auth-ring"></div>
				<div className="auth-ring"></div>
			</div>

			<div className="auth-container">
				<div className="auth-form-card auth-form-card--register">
					<h2 className="auth-title">Реєстрація</h2>
					{error && <div className="auth-error">{error}</div>}
					<form onSubmit={onSubmit} noValidate>
						<label className="auth-label">
							Ім'я
							<input
								className="auth-input"
								name="name"
								type="text"
								placeholder="Ваше ім'я"
								value={form.name}
								onChange={onChange}
								required
							/>
						</label>

						<label className="auth-label">
							Email
							<input
								className="auth-input"
								name="email"
								type="email"
								placeholder="you@example.com"
								value={form.email}
								onChange={onChange}
								required
							/>
						</label>

						<label className="auth-label">
							Пароль
							<input
								className="auth-input"
								name="password"
								type="password"
								placeholder="Пароль"
								value={form.password}
								onChange={onChange}
								required
								minLength={6}
							/>
						</label>

						<label className="auth-label">
							Підтвердження пароля
							<input
								className="auth-input"
								name="confirm"
								type="password"
								placeholder="Повторіть пароль"
								value={form.confirm}
								onChange={onChange}
								required
								minLength={6}
							/>
						</label>

						<button type="submit" disabled={loading} className="auth-button">
							{loading ? 'Реєструємо...' : 'Створити акаунт'}
						</button>
					</form>

					<div className="auth-bottom-text">
						Вже маєте акаунт? <Link to="/login">Увійти</Link>
					</div>
				</div>
			</div>
		</div>
	);
}

export default Register;
