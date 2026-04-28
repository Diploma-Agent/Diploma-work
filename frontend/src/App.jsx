import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Register from './templates/Register';
import Login from './templates/Login';
import Profile from './templates/Profile';
import Dashboard from './templates/Dashboard';
import Analytics from './templates/Analytics';
import Transactions from './templates/Transactions';
import ChatComponent from './components/ChatComponent';

const AUTH_ROUTES = ['/login', '/register'];

function AppContent() {
	const location = useLocation();
	const showChat = !AUTH_ROUTES.includes(location.pathname);

	return (
		<>
			<Routes>
				<Route path="/register" element={<Register />} />
				<Route path="/login" element={<Login />} />
				<Route path="/profile" element={<Profile />} />
				<Route path="/dashboard" element={<Dashboard />} />
				<Route path="/transactions" element={<Transactions />} />
				<Route path="/analytics" element={<Analytics />} />
				<Route path="/" element={<Navigate to="/login" />} />
			</Routes>
			{showChat && <ChatComponent />}
		</>
	);
}

function App() {
	return (
		<Router>
			<AppContent />
		</Router>
	);
}

export default App;
