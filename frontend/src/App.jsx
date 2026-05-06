import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Register from './templates/Register';
import Login from './templates/Login';
import Profile from './templates/Profile';
import Dashboard from './templates/Dashboard';
import Analytics from './templates/Analytics';
import Transactions from './templates/Transactions';
import CreateProfile from './templates/CreateProfile';
import ChatComponent from './components/ChatComponent';
import { FinanceProvider } from './context/FinanceContext';

const AUTH_ROUTES = ['/login', '/register', '/create-profile'];

const PrivateRoute = ({ children }) => {
	const isAuthenticated = localStorage.getItem('token');
	return isAuthenticated ? children : <Navigate to="/login" replace />;
};

function AppContent() {
	const location = useLocation();
	const isAuthenticated = !!localStorage.getItem('token');
	const showChat = isAuthenticated && !AUTH_ROUTES.includes(location.pathname);

	return (
		<>
			<Routes>
				<Route path="/register" element={<Register />} />
				<Route path="/login" element={<Login />} />

				<Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
				<Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
				<Route path="/create-profile" element={<PrivateRoute><CreateProfile /></PrivateRoute>} />
				<Route path="/transactions" element={<PrivateRoute><Transactions /></PrivateRoute>} />
				<Route path="/analytics" element={<PrivateRoute><Analytics /></PrivateRoute>} />
			</Routes>
			{showChat && <ChatComponent />}
		</>
	);
}

function App() {
	return (
		<Router>
			<FinanceProvider>
				<AppContent />
			</FinanceProvider>
		</Router>
	);
}

export default App;
