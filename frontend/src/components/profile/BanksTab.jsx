import React from 'react';

const BanksTab = ({
    banks,
    showAddBank,
    setShowAddBank,
    bankForm,
    onBankChange,
    handleAddBank,
    handleRemoveBank,
    handleSyncBank,
    syncingBankId
}) => {
    // Використовуємо файли з папки public/images
    const bankLogos = {
        monobank: '/images/monobank.png',
        pumb: '/images/pumb.png'
    };

    const getBankIcon = (bankType) => {
        if (!bankType) return <span style={{ fontSize: '32px' }}>🏦</span>;
        
        const logo = bankLogos[bankType.toLowerCase()];
        if (!logo) {
            return <span style={{ fontSize: '32px' }}>🏦</span>;
        }
        
        return (
            <img 
                src={logo} 
                alt={bankType} 
                className="bank-logo"
                onError={(e) => {
                    console.error('Помилка завантаження логотипу банку:', bankType, 'Шлях:', logo);
                    e.target.onerror = null;
                    e.target.style.display = 'none';
                    const parent = e.target.parentElement;
                    parent.innerHTML = '<span style="font-size: 32px">🏦</span>';
                }}
            />
        );
    };

    return (
        <div className="banks-section">
            <div className="section-header">
                <h3 className="section-title">Підключені банки</h3>
                <button
                    onClick={() => setShowAddBank(!showAddBank)}
                    className="add-button"
                >
                    {showAddBank ? '✕ Скасувати' : '+ Додати банк'}
                </button>
            </div>

            {showAddBank && (
                <form onSubmit={handleAddBank} className="add-form">
                    <label className="profile-label">
                        <span>Назва банку</span>
                        <input
                            className="profile-input"
                            name="name"
                            type="text"
                            placeholder="Наприклад: Мій ПУМБ"
                            value={bankForm.name}
                            onChange={onBankChange}
                            required
                        />
                    </label>

                    <label className="profile-label">
                        <span>Тип банку</span>
                        <select
                            className="profile-input"
                            name="type"
                            value={bankForm.type}
                            onChange={onBankChange}
                        >
                            <option value="monobank">Monobank</option>
                            <option value="pumb">ПУМБ</option>
                        </select>
                    </label>

                    <label className="profile-label">
                        <span>API ключ</span>
                        <input
                            className="profile-input"
                            name="apiKey"
                            type="password"
                            placeholder="Введіть API ключ банку"
                            value={bankForm.apiKey}
                            onChange={onBankChange}
                            required
                        />
                    </label>

                    <button type="submit" className="profile-button profile-button--save">
                        Додати банк
                    </button>
                </form>
            )}

            <div className="items-list">
                {banks.length === 0 ? (
                    <div className="empty-state">
                        <span className="empty-icon">🏦</span>
                        <p>Ще немає підключених банків</p>
                        <p className="empty-hint">Додайте банк для автоматичної синхронізації транзакцій</p>
                    </div>
                ) : (
                    banks.map(bank => (
                        <div key={bank.id} className="item-card">
                            <div className="item-icon">
                                {getBankIcon(bank.bank_name)}
                            </div>
                            <div className="item-info">
                                <h4 className="item-name">{bank.name}</h4>
                                <p className="item-detail">{bank.bank_name?.toUpperCase()}</p>
                                <p className="item-date">
                                    Додано: {new Date(bank.created_at).toLocaleDateString('uk-UA')}
                                </p>
                                <span className={`item-status ${bank.status}`}>
                                    {bank.status === 'active' ? '● Активний' : '○ Неактивний'}
                                </span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                <button
                                    onClick={() => handleSyncBank(bank)}
                                    className="remove-button"
                                    title="Синхронізувати транзакції"
                                    disabled={syncingBankId === bank.id}
                                    style={{ background: syncingBankId === bank.id ? '#a0aec0' : '#48bb78', color: '#fff', border: 'none' }}
                                >
                                    {syncingBankId === bank.id ? '⏳' : '🔄'}
                                </button>
                                <button
                                    onClick={() => handleRemoveBank(bank.id)}
                                    className="remove-button"
                                    title="Видалити"
                                >
                                    🗑️
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default BanksTab;
