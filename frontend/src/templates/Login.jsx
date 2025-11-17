import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/authStyles.css';
import { authService } from '../api/authService';

function Login() {
	const [form, setForm] = useState({ email: '', password: '' });
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(false);
	const navigate = useNavigate();

	const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

	const onSubmit = async (e) => {
		e.preventDefault();
		setError('');

		if (!form.email || !form.password) {
			setError('Заповніть всі поля.');
			return;
		}

		try {
			setLoading(true);
			
			// Використовуємо реальний API
			const data = await authService.login({
				email: form.email,
				password: form.password,
			});
			
			if (data.token) {
				// Токен вже збережено в authService.login
				navigate('/dashboard');
			} else {
				throw new Error('Токен не отримано');
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
				<div className="auth-form-card auth-form-card--login">
					<h2 className="auth-title">Вхід</h2>
					{error && <div className="auth-error">{error}</div>}
					<form onSubmit={onSubmit} noValidate>
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
							/>
						</label>

						<button type="submit" disabled={loading} className="auth-button">
							{loading ? 'Входимо...' : 'Увійти'}
						</button>
					</form>

					<div className="auth-bottom-text">
						Немає акаунта? <Link to="/register">Зареєструватися</Link>
					</div>
				</div>
			</div>
		</div>
	);
}

export default Login;
