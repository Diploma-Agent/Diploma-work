import React, { useState, useEffect } from 'react';
import { financeService } from '../../api/financeService';

const TokensTab = () => {
    const [tokens, setTokens] = useState([]);
    const [showAddToken, setShowAddToken] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [tokenForm, setTokenForm] = useState({
        exchange: 'binance',
        apiKey: '',
        apiSecret: '',
        name: ''
    });

    useEffect(() => {
        loadTokens();
    }, []);

    const loadTokens = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;
            const data = await financeService.getExchanges(token);
            setTokens(data);
        } catch (err) {
            console.error('Помилка завантаження бірж:', err);
            // Не показуємо помилку користувачу при першому завантаженні, якщо просто немає даних
        }
    };

    const onTokenChange = (e) => {
        setTokenForm({ ...tokenForm, [e.target.name]: e.target.value });
    };

    const handleAddToken = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!tokenForm.name || !tokenForm.apiKey || !tokenForm.apiSecret) {
            setError('Заповніть всі поля токена.');
            return;
        }

        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            await financeService.addExchange(token, tokenForm);
            
            setTokenForm({ exchange: 'binance', apiKey: '', apiSecret: '', name: '' });
            setShowAddToken(false);
            setSuccess('Токен біржі успішно додано!');
            loadTokens();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRemoveToken = async (id) => {
        if (!window.confirm('Ви впевнені, що хочете видалити цей токен?')) return;

        try {
            const token = localStorage.getItem('token');
            await financeService.deleteExchange(token, id);
            setSuccess('Токен видалено!');
            loadTokens();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError(err.message);
        }
    };

    // Використовуємо файли з папки public/images
    const exchangeLogos = {
        binance: '/images/binance.png',
        bybit: '/images/bybit.png',
        whitebit: '/images/whitebit.png',
        okx: '/images/okx.png'
    };

    const getExchangeIcon = (exchange) => {
        const logo = exchangeLogos[exchange];
        if (!logo) {
            return <span style={{ fontSize: '32px' }}>🪙</span>;
        }
        
        return (
            <img 
                src={logo} 
                alt={exchange} 
                className="bank-logo"
                onError={(e) => {
                    console.error('Помилка завантаження логотипу біржі:', exchange, 'Шлях:', logo);
                    e.target.onerror = null;
                    e.target.style.display = 'none';
                    const parent = e.target.parentElement;
                    parent.innerHTML = '<span style="font-size: 32px">🪙</span>';
                }}
            />
        );
    };

    return (
        <div className="tokens-section">
            <div className="section-header">
                <h3 className="section-title">API Ключі Бірж</h3>
                <button
                    onClick={() => setShowAddToken(!showAddToken)}
                    className="add-button"
                >
                    {showAddToken ? '✕ Скасувати' : '+ Додати ключ'}
                </button>
            </div>

            {error && <div className="error-message" style={{marginBottom: '15px'}}>{error}</div>}
            {success && <div className="success-message" style={{marginBottom: '15px'}}>{success}</div>}

            {showAddToken && (
                <form onSubmit={handleAddToken} className="add-form">
                    <label className="profile-label">
                        <span>Назва ключа</span>
                        <input
                            className="profile-input"
                            name="name"
                            type="text"
                            placeholder="Наприклад: Мій Bybit"
                            value={tokenForm.name}
                            onChange={onTokenChange}
                            required
                        />
                    </label>

                    <label className="profile-label">
                        <span>Біржа</span>
                        <select
                            className="profile-input"
                            name="exchange"
                            value={tokenForm.exchange}
                            onChange={onTokenChange}
                        >
                            <option value="bybit">Bybit</option>
                            <option value="binance">Binance</option>
                            <option value="whitebit">WhiteBIT</option>
                            <option value="okx">OKX</option>
                        </select>
                    </label>

                    <label className="profile-label">
                        <span>API Key</span>
                        <input
                            className="profile-input"
                            name="apiKey"
                            type="text"
                            placeholder="Введіть API Key"
                            value={tokenForm.apiKey}
                            onChange={onTokenChange}
                            required
                        />
                    </label>

                    <label className="profile-label">
                        <span>API Secret</span>
                        <input
                            className="profile-input"
                            name="apiSecret"
                            type="password"
                            placeholder="Введіть API Secret"
                            value={tokenForm.apiSecret}
                            onChange={onTokenChange}
                            required
                        />
                        <small className="input-hint">
                            ⚠️ Ключі зберігаються локально та не передаються на сервер
                        </small>
                    </label>

                    <button type="submit" className="profile-button profile-button--save" disabled={loading}>
                        {loading ? 'Збереження...' : 'Зберегти ключ'}
                    </button>
                </form>
            )}

            <div className="items-list">
                {tokens.length === 0 ? (
                    <div className="empty-state">
                        <span className="empty-icon">🔑</span>
                        <p>Ще немає доданих API ключів</p>
                        <p className="empty-hint">Додайте ключі бірж для відстеження балансів та торгівлі</p>
                    </div>
                ) : (
                    tokens.map(token => (
                        <div key={token.id} className="item-card">
                            <div className="item-icon">
                                {getExchangeIcon(token.exchange)}
                            </div>
                            <div className="item-info">
                                <h4 className="item-name">{token.name}</h4>
                                <p className="item-detail">{token.exchange?.toUpperCase()}</p>
                                <p className="item-detail token-value">
                                    API Key: {token.api_key_masked || 'Захищено'}
                                </p>
                                <p className="item-date">
                                    Додано: {new Date(token.created_at).toLocaleDateString('uk-UA')}
                                </p>
                                <span className={`item-status ${token.status}`}>
                                    {token.status === 'active' ? '● Активний' : '○ Неактивний'}
                                </span>
                            </div>
                            <button
                                onClick={() => handleRemoveToken(token.id)}
                                className="remove-button"
                                title="Видалити"
                            >
                                🗑️
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default TokensTab;
