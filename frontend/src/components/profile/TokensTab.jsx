import React, { useState, useEffect } from 'react';
import { financeService } from '../../api/financeService';

/* ── Інструкції для кожної біржі ── */
const EXCHANGE_INSTRUCTIONS = {
    binance: {
        icon: '🟡',
        title: 'Як отримати API ключ Binance',
        steps: [
            'Увійдіть на binance.com та перейдіть: Профіль → API Management',
            'Натисніть «Create API» → виберіть «System generated»',
            'Назвіть ключ та підтвердьте через email/2FA',
            'У розділі «API restrictions» увімкніть Enable Reading',
            'У розділі «IP access restrictions» оберіть «Restrict access to trusted IPs» та додайте IP сервера нижче',
            'Скопіюйте API Key та Secret Key (Secret показується лише раз!)',
        ],
        warning: '⚠️ Додайте IP сервера у whitelist Binance, інакше запити будуть заблоковані.',
        link: { label: 'Відкрити API Management', url: 'https://www.binance.com/en/my/settings/api-management' },
        showServerIp: true,
    },
    bybit: {
        icon: '🟠',
        title: 'Як отримати API ключ Bybit',
        steps: [
            'Увійдіть на bybit.com та перейдіть: My Account → API',
            'Натисніть «Create New Key»',
            'Виберіть тип: API Transaction → Read-Only',
            'IP Restriction: можна залишити «No IP restriction» (рекомендується обмежити)',
            'Скопіюйте API Key та Secret Key',
        ],
        warning: null,
        link: { label: 'Відкрити API Management', url: 'https://www.bybit.com/app/user/api-management' },
        showServerIp: false,
    },
    okx: {
        icon: '⚫',
        title: 'Як отримати API ключ OKX',
        steps: [
            'Увійдіть на okx.com та перейдіть: Профіль → API',
            'Натисніть «Create API Key»',
            'Виберіть права: Read → підтвердьте через 2FA',
            'Обов\'язково задайте Passphrase — запам\'ятайте його!',
            'Скопіюйте API Key, Secret Key та Passphrase',
        ],
        warning: '⚠️ Passphrase вводиться лише при створенні і не відновлюється — збережіть його.',
        link: { label: 'Відкрити API Management', url: 'https://www.okx.com/account/users/personal-center/manage-api' },
        showServerIp: false,
    },
};

/* ── Попап з інструкціями ── */
const InstructionPopup = ({ exchange, onClose }) => {
    const info = EXCHANGE_INSTRUCTIONS[exchange];
    const [serverIp, setServerIp] = useState(null);
    const [ipLoading, setIpLoading] = useState(false);

    useEffect(() => {
        if (!info?.showServerIp) return;
        setIpLoading(true);
        fetch('/api/server-ip/')
            .then(r => r.json())
            .then(d => setServerIp(d.server_outbound_ip))
            .catch(() => setServerIp('недоступний'))
            .finally(() => setIpLoading(false));
    }, [exchange]);

    if (!info) return null;

    return (
        <div className="instruction-overlay" onClick={onClose}>
            <div className="instruction-popup" onClick={e => e.stopPropagation()}>
                <div className="instruction-header">
                    <span className="instruction-icon">{info.icon}</span>
                    <h3 className="instruction-title">{info.title}</h3>
                    <button className="instruction-close" onClick={onClose}>✕</button>
                </div>

                <ol className="instruction-steps">
                    {info.steps.map((step, i) => (
                        <li key={i}>{step}</li>
                    ))}
                </ol>

                {info.showServerIp && (
                    <div className="instruction-server-ip">
                        <span className="ip-label">🖥 IP сервера для whitelist:</span>
                        {ipLoading ? (
                            <span className="ip-value ip-loading">Завантаження...</span>
                        ) : (
                            <span
                                className="ip-value ip-copyable"
                                title="Натисніть, щоб скопіювати"
                                onClick={() => { navigator.clipboard.writeText(serverIp); }}
                            >
                                {serverIp} <span className="ip-copy-hint">📋</span>
                            </span>
                        )}
                    </div>
                )}

                {info.warning && (
                    <div className="instruction-warning">{info.warning}</div>
                )}

                <a
                    href={info.link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="instruction-link"
                >
                    {info.link.label} ↗
                </a>
            </div>
        </div>
    );
};

/* ── Основний компонент ── */
const TokensTab = () => {
    const [tokens, setTokens] = useState([]);
    const [showAddToken, setShowAddToken] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showInstruction, setShowInstruction] = useState(false);
    const [tokenForm, setTokenForm] = useState({
        exchange: 'binance',
        apiKey: '',
        apiSecret: '',
        name: '',
        passphrase: '',
    });

    useEffect(() => { loadTokens(); }, []);

    const loadTokens = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;
            const data = await financeService.getExchanges(token);
            setTokens(data);
        } catch (err) {
            console.error('Помилка завантаження бірж:', err);
        }
    };

    const onTokenChange = (e) => {
        setTokenForm({ ...tokenForm, [e.target.name]: e.target.value });
    };

    const handleAddToken = async (e) => {
        e.preventDefault();
        setError(''); setSuccess('');
        if (!tokenForm.name || !tokenForm.apiKey || !tokenForm.apiSecret) {
            setError('Заповніть всі поля.');
            return;
        }
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            await financeService.addExchange(token, tokenForm);
            setTokenForm({ exchange: 'binance', apiKey: '', apiSecret: '', name: '', passphrase: '' });
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
        if (!window.confirm('Видалити цей ключ?')) return;
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

    const exchangeLogos = {
        binance: '/images/binance.png',
        bybit: '/images/bybit.png',
        okx: '/images/okx.png',
    };

    const getExchangeIcon = (exchange) => {
        const logo = exchangeLogos[exchange?.toLowerCase()];
        if (!logo) return <span style={{ fontSize: '32px' }}>🪙</span>;
        return (
            <img src={logo} alt={exchange} className="bank-logo"
                onError={e => {
                    e.target.onerror = null; e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<span style="font-size:32px">🪙</span>';
                }}
            />
        );
    };

    return (
        <div className="tokens-section">
            {showInstruction && (
                <InstructionPopup
                    exchange={tokenForm.exchange}
                    onClose={() => setShowInstruction(false)}
                />
            )}

            <div className="section-header">
                <h3 className="section-title">API Ключі Бірж</h3>
                <button onClick={() => setShowAddToken(!showAddToken)} className="add-button">
                    {showAddToken ? '✕ Скасувати' : '+ Додати ключ'}
                </button>
            </div>

            {error && <div className="error-message" style={{ marginBottom: 15 }}>{error}</div>}
            {success && <div className="success-message" style={{ marginBottom: 15 }}>{success}</div>}

            {showAddToken && (
                <form onSubmit={handleAddToken} className="add-form">
                    {/* Рядок: вибір біржі + кнопка інструкції */}
                    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
                        <label className="profile-label" style={{ flex: 1 }}>
                            <span>Біржа</span>
                            <select
                                className="profile-input"
                                name="exchange"
                                value={tokenForm.exchange}
                                onChange={onTokenChange}
                            >
                                <option value="binance">Binance</option>
                                <option value="bybit">Bybit</option>
                                <option value="okx">OKX</option>
                            </select>
                        </label>
                        <button
                            type="button"
                            className="instruction-trigger-btn"
                            onClick={() => setShowInstruction(true)}
                            title="Як отримати API ключ"
                        >
                            ℹ️ Інструкція
                        </button>
                    </div>

                    <label className="profile-label">
                        <span>Назва ключа</span>
                        <input className="profile-input" name="name" type="text"
                            placeholder="Наприклад: Мій Binance"
                            value={tokenForm.name} onChange={onTokenChange} required />
                    </label>

                    <label className="profile-label">
                        <span>API Key</span>
                        <input className="profile-input" name="apiKey" type="text"
                            placeholder="Введіть API Key"
                            value={tokenForm.apiKey} onChange={onTokenChange} required />
                    </label>

                    <label className="profile-label">
                        <span>API Secret</span>
                        <input className="profile-input" name="apiSecret" type="password"
                            placeholder="Введіть API Secret"
                            value={tokenForm.apiSecret} onChange={onTokenChange} required />
                    </label>

                    {tokenForm.exchange === 'okx' && (
                        <label className="profile-label">
                            <span>Passphrase</span>
                            <input className="profile-input" name="passphrase" type="password"
                                placeholder="Парольна фраза OKX"
                                value={tokenForm.passphrase || ''} onChange={onTokenChange} required />
                        </label>
                    )}

                    <small className="input-hint" style={{ display: 'block', marginTop: 10, marginBottom: 15 }}>
                        🔒 API ключі зберігаються у зашифрованому вигляді.
                    </small>

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
                        <p className="empty-hint">Додайте ключі бірж для відстеження балансів</p>
                    </div>
                ) : tokens.map(token => (
                    <div key={token.id} className="item-card">
                        <div className="item-icon">{getExchangeIcon(token.exchange_name)}</div>
                        <div className="item-info">
                            <h4 className="item-name">{token.name}</h4>
                            <p className="item-detail">{token.exchange_name?.toUpperCase()}</p>
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
                        <button onClick={() => handleRemoveToken(token.id)} className="remove-button" title="Видалити">
                            🗑️
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TokensTab;
