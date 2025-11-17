import axios from 'axios';

// Автоматично визначає baseURL залежно від середовища
// В dev режимі використовуємо proxy, в production - повний URL
const baseURL = import.meta.env.MODE === 'production' 
  ? window.location.origin 
  : ''; // Порожній рядок для використання proxy в dev режимі

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
