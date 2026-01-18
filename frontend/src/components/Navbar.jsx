import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../api/authService';
import '../styles/navbarStyles.css';

function Navbar() {
	const navigate = useNavigate();
	const [userName, setUserName] = useState('Користувач');

	useEffect(() => {
		const fetchUserProfile = async () => {
			const token = localStorage.getItem('token');
			if (!token) return;

			try {
				// Спочатку перевіряємо чи є збережені дані
				const savedUser = JSON.parse(localStorage.getItem('user_profile') || '{}');
				if (savedUser.first_name || savedUser.username) {
					setUserName(savedUser.first_name || savedUser.username);
				}

				// Оновлюємо дані з сервера
				const userData = await authService.getMe(token);
				const name = userData.first_name || userData.username || userData.email;
				setUserName(name);
				
				// Зберігаємо оновлені дані
				localStorage.setItem('user_profile', JSON.stringify(userData));
			} catch (error) {
				console.error('Помилка завантаження профілю:', error);
			}
		};

		fetchUserProfile();
	}, []);

	const handleLogout = () => {
		localStorage.removeItem('token');
		localStorage.removeItem('user_profile');
		localStorage.removeItem('refreshToken');
		navigate('/login');
	};

	return (
		<nav className="navbar">
			<div className="navbar-container">
				<Link to="/dashboard" className="navbar-logo">
					💰 BanFin
				</Link>

				<div className="navbar-menu">
					<Link to="/dashboard" className="navbar-link">
						📊 Головна
					</Link>
					<Link to="/profile" className="navbar-link">
						👤 Профіль
					</Link>
					<Link to="/transactions" className="navbar-link">
						💳 Транзакції
					</Link>
					<Link to="/analytics" className="navbar-link">
						📈 Аналітика
					</Link>
				</div>

				<div className="navbar-user">
					<span className="navbar-username">{userName}</span>
					<button onClick={handleLogout} className="navbar-logout">
						Вийти
					</button>
				</div>
			</div>
		</nav>
	);
}

export default Navbar;
