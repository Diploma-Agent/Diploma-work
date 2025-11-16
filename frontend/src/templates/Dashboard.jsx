import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import '../styles/dashboardStyles.css';

function Dashboard() {
	const navigate = useNavigate();

	useEffect(() => {
		const token = localStorage.getItem('token');
		if (!token) {
			navigate('/login');
		}
	}, [navigate]);

	return (
		<div className="dashboard-wrapper">
			<Navbar />
			
			<div className="dashboard-container">
				<div className="dashboard-main-box">
					<h1 className="dashboard-title">Ласкаво просимо до BanFin! 💰</h1>
					<p className="dashboard-subtitle">
						Ваш особистий помічник у керуванні фінансами
					</p>

					<div className="dashboard-grid">
						<div className="dashboard-card">
							<div className="card-icon">💳</div>
							<h3 className="card-title">Транзакції</h3>
							<p className="card-description">
								Переглядайте та керуйте всіма вашими фінансовими операціями
							</p>
						</div>

						<div className="dashboard-card">
							<div className="card-icon">📊</div>
							<h3 className="card-title">Аналітика</h3>
							<p className="card-description">
								Детальна статистика та візуалізація ваших витрат
							</p>
						</div>

						<div className="dashboard-card">
							<div className="card-icon">🏦</div>
							<h3 className="card-title">Банки</h3>
							<p className="card-description">
								Синхронізація з вашими банківськими рахунками
							</p>
						</div>

						<div className="dashboard-card">
							<div className="card-icon">🔑</div>
							<h3 className="card-title">Біржі</h3>
							<p className="card-description">
								Відстежуйте баланс криптовалютних активів
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}

export default Dashboard;
