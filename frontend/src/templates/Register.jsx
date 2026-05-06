import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/authStyles.css';
import { authService } from '../api/authService';

function Register() {
	const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(false);
	const [touched, setTouched] = useState({ password: false });
	const navigate = useNavigate();

	const validatePassword = (password) => {
		const errors = [];
		if (password.length < 8) {
			errors.push("Мінімум 8 символів");
		}
		if (!/\d/.test(password)) {
			errors.push("Має містити хоча б одну цифру");
		}
		if (!/[a-zA-Z]/.test(password)) {
			errors.push("Має містити хоча б одну літеру");
			}
			
			// Перевірка на прості паролі
			const commonPasswords = ['password', 'qwerty', '12345678', 'admin', 'letmein', 'welcome'];
			const lowerPassword = password.toLowerCase();
			if (commonPasswords.some(common => lowerPassword.includes(common))) {
				errors.push("Пароль занадто простий");
			}
			
			return errors;
		};

	const passwordErrors = touched.password ? validatePassword(form.password) : [];
	const isPasswordValid = form.password && passwordErrors.length === 0;

	const onChange = (e) => {
		setForm({ ...form, [e.target.name]: e.target.value });
		setError('');
	};

	const onBlur = (e) => {
		setTouched({ ...touched, [e.target.name]: true });
	};

	const onSubmit = async (e) => {
		e.preventDefault();
		setError('');

		if (!form.name || !form.email || !form.password || !form.confirm) {
			setError('Заповніть всі поля.');
			return;
		}
		
		// Перевірка валідності пароля
		const validationErrors = validatePassword(form.password);
		if (validationErrors.length > 0) {
			setError('Пароль не відповідає вимогам.');
			setTouched({ ...touched, password: true });
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
			
			const loginData = await authService.login({
				email: form.email,
				password: form.password,
			});
			
			if (loginData.token) {
				navigate('/');
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
								className={`auth-input ${touched.password && passwordErrors.length > 0 ? 'auth-input--error' : ''} ${isPasswordValid ? 'auth-input--success' : ''}`}
								name="password"
								type="password"
								placeholder="Пароль"
								value={form.password}
								onChange={onChange}
								onBlur={onBlur}
								required
							/>
							<small className="auth-hint">
								Вимоги: мінімум 8 символів, літери та цифри
							</small>
							
							{touched.password && passwordErrors.length > 0 && (
								<ul className="auth-validation-errors">
									{passwordErrors.map((err, index) => (
										<li key={index}>✗ {err}</li>
									))}
								</ul>
							)}
							
							{isPasswordValid && (
								<div className="auth-validation-success">
									✓ Пароль відповідає вимогам
								</div>
							)}
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
