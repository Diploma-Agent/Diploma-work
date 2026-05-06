import axios from 'axios';

// В dev — порожній рядок: Vite proxy перенаправляє /api/* → localhost:8000
// В production — VITE_API_BASE_URL вказує на Render backend URL
const baseURL = import.meta.env.VITE_API_BASE_URL || '';

const instance = axios.create({
  baseURL,
});

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default instance;
