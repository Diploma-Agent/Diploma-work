import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';

/* ── Інструкції для Monobank ── */
const BANK_INSTRUCTIONS = {
    monobank: {
        icon: '🖤',
        title: 'Як отримати токен Monobank',
        steps: [
            'Відкрийте додаток Monobank на смартфоні',
            'Перейдіть: Профіль (іконка людини) → API → Видати токен',
            'Або натисніть посилання нижче і авторизуйтесь через вебсайт',
            'Токен дійсний безстроково — зберігайте його у безпечному місці',
            'Скопіюйте токен і вставте в поле «API ключ»',
        ],
        warning: null,
        link: { label: 'Відкрити Monobank API', url: 'https://api.monobank.ua/' },
    },
};

/* ── Попап (через Portal → завжди в центрі видимого екрана) ── */
const InstructionPopup = ({ bankType, onClose }) => {
    const info = BANK_INSTRUCTIONS[bankType] || BANK_INSTRUCTIONS.monobank;

    useEffect(() => {
        const onKey = e => { if (e.key === 'Escape') onClose(); };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [onClose]);

    const popup = (
        <div className="instruction-overlay" onClick={onClose}>
            <div className="instruction-popup" onClick={e => e.stopPropagation()}>
                <div className="instruction-header">
                    <span className="instruction-icon">{info.icon}</span>
                    <h3 className="instruction-title">{info.title}</h3>
                    <button className="instruction-close" onClick={onClose}>✕</button>
                </div>

                <ol className="instruction-steps">
                    {info.steps.map((step, i) => <li key={i}>{step}</li>)}
                </ol>

                {info.warning && <div className="instruction-warning">{info.warning}</div>}

                <a href={info.link.url} target="_blank" rel="noopener noreferrer" className="instruction-link">
                    {info.link.label} ↗
                </a>
            </div>
        </div>
    );

    return ReactDOM.createPortal(popup, document.body);
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
    addingBank,
}) => {
    const [showInstruction, setShowInstruction] = useState(false);

    const getBankIcon = (bankType) => {
        if (bankType?.toLowerCase() === 'monobank') {
            return (
                <img src="/images/monobank.png" alt="monobank" className="bank-logo"
                    onError={e => {
                        e.target.onerror = null; e.target.style.display = 'none';
                        e.target.parentElement.innerHTML = '<span style="font-size:32px">🏦</span>';
                    }}
                />
            );
        }
        return <span style={{ fontSize: '32px' }}>🏦</span>;
    };

    return (
        <div className="banks-section">
            {showInstruction && (
                <InstructionPopup
                    bankType="monobank"
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
                            placeholder="Введіть токен з додатку Monobank"
                            value={bankForm.apiKey} onChange={onBankChange} required />
                    </label>

                    <small className="input-hint" style={{ display: 'block', marginTop: 10, marginBottom: 15 }}>
                        🔒 Токен зберігається у зашифрованому вигляді.
                    </small>

                    <button
                        type="submit"
                        className="profile-button profile-button--save"
                        disabled={addingBank}
                        style={{ position: 'relative', minWidth: 140 }}
                    >
                        {addingBank ? (
                            <span className="btn-loading-inner">
                                <span className="btn-spinner" />
                                Перевірка токена...
                            </span>
                        ) : 'Додати банк'}
                    </button>
                </form>
            )}

            <div className="items-list">
                {banks.length === 0 ? (
                    <div className="empty-state">
                        <span className="empty-icon">🏦</span>
                        <p>Ще немає підключених банків</p>
                        <p className="empty-hint">Додайте Monobank для автоматичної синхронізації транзакцій</p>
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
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <button
                                onClick={() => handleRemoveBank(bank.id)}
                                className="remove-button"
                                title="Видалити підключення та транзакції"
                            >
                                🗑️
                            </button>
                            <button
                                onClick={() => handleSyncBank(bank)}
                                className="remove-button"
                                title="Примусова синхронізація (транзакції оновлюються автоматично щогодини)"
                                disabled={syncingBankId === bank.id}
                                style={{
                                    background: 'transparent',
                                    color: syncingBankId === bank.id ? '#64748b' : '#475569',
                                    border: '1px solid #334155',
                                    fontSize: '13px',
                                }}
                            >
                                {syncingBankId === bank.id ? '⏳' : '↻'}
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {banks.length > 0 && (
                <p style={{
                    marginTop: 16, textAlign: 'center',
                    fontSize: 12, color: '#475569',
                }}>
                    🔄 Транзакції оновлюються автоматично щогодини. Кнопка ↻ — лише для примусового оновлення.
                </p>
            )}
        </div>
    );
};

export default BanksTab;
