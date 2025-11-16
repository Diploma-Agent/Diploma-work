import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/navbarStyles.css';

function Navbar() {
	const navigate = useNavigate();
	const user = JSON.parse(localStorage.getItem('mockUser') || '{}');

	const handleLogout = () => {
		localStorage.removeItem('token');
		localStorage.removeItem('mockUser');
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
					<span className="navbar-username">{user.name || 'Користувач'}</span>
					<button onClick={handleLogout} className="navbar-logout">
						Вийти
					</button>
				</div>
			</div>
		</nav>
	);
}

export default Navbar;
