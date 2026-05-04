import React from 'react';

const ProfileTab = ({ 
    user, 
    editMode, 
    setEditMode, 
    form, 
    onChange, 
    onSubmit, 
    loading, 
    onCancelEdit, 
    handleLogout 
}) => {
    return (
        <>
            <div className="profile-header">
                <div className="profile-avatar">
                    {user.first_name?.charAt(0).toUpperCase() || user.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <h2 className="profile-name">{user.first_name || user.username}</h2>
                <p className="profile-email">{user.email}</p>
            </div>

            {editMode ? (
                <form onSubmit={onSubmit} className="profile-form">
                    <label className="profile-label">
                        <span>Ім'я *</span>
                        <input
                            className="profile-input"
                            name="name"
                            type="text"
                            placeholder="Ваше ім'я"
                            value={form.name}
                            onChange={onChange}
                            required
                        />
                    </label>

                    <label className="profile-label">
                        <span>Email *</span>
                        <input
                            className="profile-input"
                            name="email"
                            type="email"
                            placeholder="you@example.com"
                            value={form.email}
                            onChange={onChange}
                            required
                        />
                    </label>

                    <label className="profile-label">
                        <span>Телефон</span>
                        <input
                            className="profile-input profile-input--phone"
                            name="phone"
                            type="tel"
                            placeholder="+380 (XX) XXX-XX-XX"
                            value={form.phone}
                            onChange={onChange}
                        />
                    </label>

                    <label className="profile-label">
                        <span>Дата народження</span>
                        <input
                            className="profile-input"
                            name="dateOfBirth"
                            type="date"
                            value={form.dateOfBirth}
                            onChange={onChange}
                        />
                    </label>

                    <label className="profile-label">
                        <span>Місцезнаходження</span>
                        <input
                            className="profile-input profile-input--location"
                            name="location"
                            type="text"
                            placeholder="Київ, Україна"
                            value={form.location}
                            onChange={onChange}
                        />
                    </label>

                    <label className="profile-label">
                        <span>Біографія</span>
                        <textarea
                            className="profile-input profile-textarea"
                            name="bio"
                            placeholder="Розкажіть про себе..."
                            value={form.bio}
                            onChange={onChange}
                            maxLength={500}
                        />
                        <span className={`char-counter ${form.bio.length > 450 ? 'warning' : ''} ${form.bio.length >= 500 ? 'error' : ''}`}>
                            {form.bio.length}/500
                        </span>
                    </label>

                    <hr className="profile-section-divider" />

                    <h4 className="profile-subsection-title">Соціальні мережі</h4>

                    <div className="social-links-group">
                        <label className="profile-label">
                            <span>Telegram</span>
                            <input
                                className="profile-input profile-input--telegram"
                                name="telegram"
                                type="text"
                                placeholder="@username"
                                value={form.telegram}
                                onChange={onChange}
                            />
                        </label>

                        <label className="profile-label">
                            <span>LinkedIn</span>
                            <input
                                className="profile-input profile-input--linkedin"
                                name="linkedin"
                                type="url"
                                placeholder="https://linkedin.com/in/username"
                                value={form.linkedin}
                                onChange={onChange}
                            />
                        </label>
                    </div>

                    <div className="profile-buttons">
                        <button
                            type="submit"
                            disabled={loading}
                            className="profile-button profile-button--save"
                        >
                            {loading ? 'Збереження...' : 'Зберегти'}
                        </button>
                        <button
                            type="button"
                            onClick={onCancelEdit}
                            className="profile-button profile-button--cancel"
                        >
                            Скасувати
                        </button>
                    </div>
                </form>
            ) : (
                <>
                    <div className="profile-info-grid">
                        <div className="profile-info-card">
                            <span className="profile-info-label">Телефон</span>
                            <div className={`profile-info-value ${!user.phone ? 'empty' : ''}`}>
                                {user.phone || 'Не вказано'}
                            </div>
                        </div>

                        <div className="profile-info-card">
                            <span className="profile-info-label">Дата народження</span>
                            <div className={`profile-info-value ${!user.dateOfBirth ? 'empty' : ''}`}>
                                {user.dateOfBirth ? new Date(user.dateOfBirth).toLocaleDateString('uk-UA') : 'Не вказано'}
                            </div>
                        </div>

                        <div className="profile-info-card">
                            <span className="profile-info-label">Місцезнаходження</span>
                            <div className={`profile-info-value ${!user.location ? 'empty' : ''}`}>
                                {user.location || 'Не вказано'}
                            </div>
                        </div>

                        {user.bio && (
                            <div className="profile-info-card" style={{ gridColumn: '1 / -1' }}>
                                <span className="profile-info-label">Про себе</span>
                                <div className="profile-info-value">{user.bio}</div>
                            </div>
                        )}

                        {(user.telegram || user.linkedin) && (
                            <>
                                <div className="profile-info-card">
                                    <span className="profile-info-label">Telegram</span>
                                    <div className={`profile-info-value ${!user.telegram ? 'empty' : ''}`}>
                                        {user.telegram || 'Не вказано'}
                                    </div>
                                </div>

                                <div className="profile-info-card">
                                    <span className="profile-info-label">LinkedIn</span>
                                    <div className={`profile-info-value ${!user.linkedin ? 'empty' : ''}`}>
                                        {user.linkedin ? (
                                            <a href={user.linkedin} target="_blank" rel="noopener noreferrer" style={{ color: '#667eea' }}>
                                                Профіль
                                            </a>
                                        ) : 'Не вказано'}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    <div className="profile-actions">
                        <button
                            onClick={() => setEditMode(true)}
                            className="profile-button profile-button--edit"
                        >
                            Редагувати профіль
                        </button>
                        <button
                            onClick={handleLogout}
                            className="profile-button profile-button--logout"
                        >
                            Вийти
                        </button>
                    </div>
                </>
            )}

            <div className="profile-info">
                <p className="profile-info-item">
                    <strong>Дата реєстрації:</strong>{' '}
                    {new Date(user.date_joined || user.createdAt || Date.now()).toLocaleDateString('uk-UA')}
                </p>
            </div>
        </>
    );
};

export default ProfileTab;
