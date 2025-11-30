import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { financeService } from '../api/financeService';
import '../styles/analyticsStyles.css';

const Analytics = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [balance, setBalance] = useState(null);
    const [spotOrders, setSpotOrders] = useState([]);
    const [futuresOrders, setFuturesOrders] = useState([]);
    const [selectedExchange, setSelectedExchange] = useState('bybit');
    const [exchanges, setExchanges] = useState([]);
    const [activeTab, setActiveTab] = useState('spot');

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }

        const fetchExchanges = async () => {
            try {
                const data = await financeService.getExchanges(token);
                setExchanges(data);
                if (data.length > 0) {
                    const currentExists = data.some(e => e.exchange_name === selectedExchange);
                    if (!currentExists) {
                        setSelectedExchange(data[0].exchange_name);
                    }
                }
            } catch (err) {
                console.error('Error fetching exchanges:', err);
            }
        };

        fetchExchanges();
    }, [navigate]);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) return;

        const fetchData = async () => {
            setLoading(true);
            setError('');
            try {
                // Fetch Balance
                const balanceData = await financeService.getExchangeBalance(token, selectedExchange);
                setBalance(balanceData);
    
                // Fetch Spot Orders
                const spotData = await financeService.getExchangeOrders(token, selectedExchange, 'spot');
                setSpotOrders(spotData.list || []);

                // Fetch Futures Orders (Linear)
                try {
                    const futuresData = await financeService.getExchangeOrders(token, selectedExchange, 'linear');
                    setFuturesOrders(futuresData.list || []);
                } catch (e) {
                    console.warn('Failed to fetch futures orders', e);
                    setFuturesOrders([]);
                }
    
            } catch (err) {
                console.error('Error fetching analytics:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (selectedExchange) {
            fetchData();
        }
    }, [selectedExchange]);

    const renderExchangeSelector = () => {
        if (exchanges.length === 0) return null;

        return (
            <div className="exchange-selector">
                <label htmlFor="exchange-select">Оберіть біржу:</label>
                <select 
                    id="exchange-select"
                    value={selectedExchange} 
                    onChange={(e) => setSelectedExchange(e.target.value)}
                    className="exchange-select-input"
                >
                    {exchanges.map(ex => (
                        <option key={ex.id} value={ex.exchange_name}>
                            {ex.name} ({ex.exchange_name.toUpperCase()})
                        </option>
                    ))}
                </select>
            </div>
        );
    };

    const renderBalance = () => {
        if (!balance || !balance.list?.[0]) return (
            <div className="analytics-card balance-card">
                <h3>💰 Баланс ({selectedExchange.toUpperCase()})</h3>
                <div className="no-data">Немає даних про баланс</div>
            </div>
        );
        
        const account = balance.list[0];
        const coins = account.coin || [];

        return (
            <div className="analytics-card balance-card">
                <h3>💰 Баланс ({selectedExchange.toUpperCase()})</h3>
                <div className="total-equity">
                    <span className="label">Загальний капітал:</span>
                    <span className="value">{parseFloat(account.totalEquity).toFixed(2)} USD</span>
                </div>
                <div className="coins-grid">
                    {coins.filter(c => parseFloat(c.walletBalance) > 0).map(coin => (
                        <div key={coin.coin} className="coin-item">
                            <span className="coin-name">{coin.coin}</span>
                            <span className="coin-value">{parseFloat(coin.walletBalance).toFixed(4)}</span>
                            <span className="coin-usd">≈ {parseFloat(coin.usdValue).toFixed(2)} $</span>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const renderOrders = () => {
        const currentOrders = activeTab === 'spot' ? spotOrders : futuresOrders;
        const title = activeTab === 'spot' ? 'Spot Ордери' : 'Futures Ордери';
        const icon = activeTab === 'spot' ? '📋' : '📈';

        return (
            <div className="analytics-card orders-card">
                <div className="orders-header-tabs">
                    <button 
                        className={`tab-button ${activeTab === 'spot' ? 'active' : ''}`}
                        onClick={() => setActiveTab('spot')}
                    >
                        Spot
                    </button>
                    <button 
                        className={`tab-button ${activeTab === 'futures' ? 'active' : ''}`}
                        onClick={() => setActiveTab('futures')}
                    >
                        Futures
                    </button>
                </div>

                <h3>{icon} {title} ({currentOrders.length})</h3>
                
                {currentOrders.length === 0 ? (
                    <div className="no-data">Немає активних ордерів</div>
                ) : (
                    <div className="orders-list">
                        {currentOrders.map(order => (
                            <div key={order.orderId} className="order-item">
                                <div className="order-header">
                                    <span className="order-symbol">{order.symbol}</span>
                                    <span className={`order-side ${order.side.toLowerCase()}`}>{order.side}</span>
                                </div>
                                <div className="order-details">
                                    <div className="detail-row">
                                        <span>Ціна:</span>
                                        <span>{order.price}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span>Кількість:</span>
                                        <span>{order.qty}</span>
                                    </div>
                                    <div className="detail-row">
                                        <span>Тип:</span>
                                        <span>{order.orderType}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="analytics-page">
            <Navbar />
            <div className="analytics-container">
                <div className="analytics-header">
                    <h1 className="page-title">Аналітика Біржі</h1>
                    {renderExchangeSelector()}
                </div>
                
                {error && <div className="error-message">{error}</div>}
                
                {loading ? (
                    <div className="loading-spinner">Завантаження даних...</div>
                ) : (
                    <div className="analytics-grid">
                        {renderBalance()}
                        {renderOrders()}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Analytics;
