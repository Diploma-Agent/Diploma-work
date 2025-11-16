import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/homeStyles.css';

function Home() {
	return (
		<div className="home-wrapper">
			<div className="home-content">
				<h1 className="home-logo">BanFin</h1>
				<p className="home-subtitle">Ваш особистий фінансовий помічник</p>
				
				<div className="home-buttons">
					<Link to="/login" className="home-btn home-btn--login">
						<span>Увійти</span>
						<span className="home-btn-icon">→</span>
					</Link>
					
					<Link to="/register" className="home-btn home-btn--register">
						<span>Зареєструватися</span>
						<span className="home-btn-icon">→</span>
					</Link>
				</div>
			</div>
		</div>
	);
}

export default Home;
