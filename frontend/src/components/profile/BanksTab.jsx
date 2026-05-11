import React, { useState } from 'react';

/* ── Інструкції для кожного банку ── */
const BANK_INSTRUCTIONS = {
    monobank: {
        icon: '🖤',
        title: 'Як отримати токен Monobank',
        steps: [
            'Відкрийте додаток Monobank на смартфоні',
            'Перейдіть: Профіль (іконка людини) → API → Видати токен',
            'Або перейдіть за посиланням нижче та авторизуйтесь',
            'Токен дійсний безстроково — зберігайте його у безпечному місці',
            'Скопіюйте токен і вставте в поле «API ключ» вище',
        ],
        warning: null,
        link: { label: 'Відкрити Monobank API', url: 'https://api.monobank.ua/' },
    },
    pumb: {
        icon: '🔵',
        title: 'Як підключити ПУМБ',
        steps: [
            'Введіть назву підключення та ваш токен доступу ПУМБ',
            'Після збереження система автоматично перевірить токен',
            'Якщо токен не відомий — зверніться до підтримки ПУМБ або інтернет-банкінгу',
            'Токен оновлюється автоматично кожні 24 години',
        ],
        warning: '⚠️ ПУМБ API є тестовим — для реального доступу потрібна домовленість з банком.',
        link: { label: 'Відкрити ПУМБ Developer Portal', url: 'https://developer.pumb.ua/' },
    },
};

/* ── Попап з інструкціями ── */
const InstructionPopup = ({ bankType, onClose }) => {
    const info = BANK_INSTRUCTIONS[bankType] || BANK_INSTRUCTIONS.monobank;

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
const BanksTab = ({
    banks,
    showAddBank,
    setShowAddBank,
    bankForm,
    onBankChange,
    handleAddBank,
    handleRemoveBank,
    handleSyncBank,
    syncingBankId,
}) => {
    const [showInstruction, setShowInstruction] = useState(false);

    const bankLogos = {
        monobank: '/images/monobank.png',
        pumb: '/images/pumb.png',
    };

    const getBankIcon = (bankType) => {
        if (!bankType) return <span style={{ fontSize: '32px' }}>🏦</span>;
        const logo = bankLogos[bankType.toLowerCase()];
        if (!logo) return <span style={{ fontSize: '32px' }}>🏦</span>;
        return (
            <img src={logo} alt={bankType} className="bank-logo"
                onError={e => {
                    e.target.onerror = null; e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<span style="font-size:32px">🏦</span>';
                }}
            />
        );
    };

    return (
        <div className="banks-section">
            {showInstruction && (
                <InstructionPopup
                    bankType={bankForm.type}
                    onClose={() => setShowInstruction(false)}
                />
            )}

            <div className="section-header">
                <h3 className="section-title">Підключені банки</h3>
                <button onClick={() => setShowAddBank(!showAddBank)} className="add-button">
                    {showAddBank ? '✕ Скасувати' : '+ Додати банк'}
                </button>
            </div>

            {showAddBank && (
                <form onSubmit={handleAddBank} className="add-form">
                    {/* Рядок: вибір банку + кнопка інструкції */}
                    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
                        <label className="profile-label" style={{ flex: 1 }}>
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
                        <button
                            type="button"
                            className="instruction-trigger-btn"
                            onClick={() => setShowInstruction(true)}
                            title="Як отримати токен"
                        >
                            ℹ️ Інструкція
                        </button>
                    </div>

                    <label className="profile-label">
                        <span>Назва банку</span>
                        <input className="profile-input" name="name" type="text"
                            placeholder="Наприклад: Мій Monobank"
                            value={bankForm.name} onChange={onBankChange} required />
                    </label>

                    <label className="profile-label">
                        <span>API ключ / Токен</span>
                        <input className="profile-input" name="apiKey" type="password"
                            placeholder="Введіть API ключ або токен банку"
                            value={bankForm.apiKey} onChange={onBankChange} required />
                    </label>

                    <small className="input-hint" style={{ display: 'block', marginTop: 10, marginBottom: 15 }}>
                        🔒 Токен зберігається у зашифрованому вигляді.
                    </small>

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
                ) : banks.map(bank => (
                    <div key={bank.id} className="item-card">
                        <div className="item-icon">{getBankIcon(bank.bank_name)}</div>
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
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <button
                                onClick={() => handleSyncBank(bank)}
                                className="remove-button"
                                title="Синхронізувати транзакції"
                                disabled={syncingBankId === bank.id}
                                style={{
                                    background: syncingBankId === bank.id ? '#a0aec0' : '#48bb78',
                                    color: '#fff', border: 'none',
                                }}
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
                ))}
            </div>
        </div>
    );
};

export default BanksTab;
