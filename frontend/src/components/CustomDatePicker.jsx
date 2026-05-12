import React, { useState, useEffect, useRef } from 'react';
import '../styles/customDatePicker.css';

const MONTHS = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень', 'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень'];
const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'];

const CustomDatePicker = ({ value, onChange, placeholder, minDate }) => {
    const [isOpen, setIsOpen] = useState(false);
    
    // Стейт для навігації по місяцях (що зараз показує календар)
    const [currentDate, setCurrentDate] = useState(() => {
        return value ? new Date(value) : new Date();
    });

    const containerRef = useRef(null);

    // Закриття при кліку поза календарем
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Оновлення відкритого місяця, якщо value змінилося ззовні
    useEffect(() => {
        if (value) setCurrentDate(new Date(value));
    }, [value]);

    const getDaysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
    
    // Отримуємо день тижня для 1-го числа (0 = Пн, 6 = Нд)
    const getFirstDayOfMonth = (year, month) => {
        let day = new Date(year, month, 1).getDay();
        return day === 0 ? 6 : day - 1; 
    };

    const handlePrevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    };

    const handleNextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    };

    const handleDayClick = (day) => {
        const selected = new Date(Date.UTC(currentDate.getFullYear(), currentDate.getMonth(), day));
        
        // Перевірка minDate
        if (minDate && selected < new Date(minDate)) return;

        const y = selected.getUTCFullYear();
        const m = String(selected.getUTCMonth() + 1).padStart(2, '0');
        const d = String(selected.getUTCDate()).padStart(2, '0');
        
        onChange(`${y}-${m}-${d}`);
        setIsOpen(false);
    };

    const handleClear = (e) => {
        e.stopPropagation(); // Щоб не відкривався календар
        onChange('');
        setIsOpen(false);
    };

    // Форматування для відображення в інпуті (ДД.ММ.РРРР)
    const displayValue = value ? value.split('-').reverse().join('.') : '';

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);

    const isDayDisabled = (day) => {
        if (!minDate) return false;
        const checkDate = new Date(Date.UTC(year, month, day));
        return checkDate < new Date(minDate);
    };

    return (
        <div className="custom-datepicker-container" ref={containerRef}>
            <div 
                className={`custom-datepicker-input-wrapper ${isOpen ? 'active' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <input 
                    type="text" 
                    readOnly 
                    value={displayValue}
                    placeholder={placeholder}
                    className="filter-input filter-date custom-datepicker-input"
                />
                
                {value ? (
                    <span className="custom-datepicker-clear" onClick={handleClear}>✕</span>
                ) : (
                    <span className="custom-calendar-icon">📅</span>
                )}
            </div>

            {isOpen && (
                <div className="custom-datepicker-dropdown">
                    <div className="custom-datepicker-header">
                        <button type="button" onClick={handlePrevMonth}>‹</button>
                        <span>{MONTHS[month]} {year}</span>
                        <button type="button" onClick={handleNextMonth}>›</button>
                    </div>
                    
                    <div className="custom-datepicker-grid">
                        {DAYS.map(day => (
                            <div key={day} className="custom-datepicker-day-name">{day}</div>
                        ))}
                        
                        {/* Порожні клітинки до 1-го числа */}
                        {Array.from({ length: firstDay }).map((_, i) => (
                            <div key={`empty-${i}`} className="custom-datepicker-day empty"></div>
                        ))}
                        
                        {/* Дні місяця */}
                        {Array.from({ length: daysInMonth }).map((_, i) => {
                            const day = i + 1;
                            const isSelected = value && value === `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                            const disabled = isDayDisabled(day);
                            
                            return (
                                <div 
                                    key={day} 
                                    className={`custom-datepicker-day ${isSelected ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
                                    onClick={() => !disabled && handleDayClick(day)}
                                >
                                    {day}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default CustomDatePicker;