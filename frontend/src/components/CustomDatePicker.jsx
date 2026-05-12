import React, { useState, useEffect, useRef } from 'react';
import '../styles/customDatePicker.css';

const MONTHS = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень', 'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень'];
const SHORT_MONTHS = ['Січ', 'Лют', 'Бер', 'Кві', 'Тра', 'Чер', 'Лип', 'Сер', 'Вер', 'Жов', 'Лис', 'Гру'];
const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'];

// Допоміжна функція: парсить рядок 'YYYY-MM-DD' у UTC Date, щоб уникнути багів з часовими поясами
const parseDateToUTC = (dateVal) => {
    if (!dateVal) return null;
    const str = typeof dateVal === 'string' ? dateVal : dateVal.toISOString().split('T')[0];
    const [y, m, d] = str.split('-');
    return new Date(Date.UTC(y, m - 1, d));
};

const CustomDatePicker = ({ value, onChange, placeholder, minDate, maxDate }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [view, setView] = useState('days'); // 'days' | 'months'
    
    const [currentDate, setCurrentDate] = useState(() => {
        return value ? parseDateToUTC(value) : new Date();
    });

    const containerRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
                setView('days');
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => {
        if (value) setCurrentDate(parseDateToUTC(value));
    }, [value]);

    const getDaysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
    
    const getFirstDayOfMonth = (year, month) => {
        let day = new Date(year, month, 1).getDay();
        return day === 0 ? 6 : day - 1; 
    };

    const handlePrev = () => {
        if (view === 'days') {
            setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
        } else {
            setCurrentDate(new Date(currentDate.getFullYear() - 1, currentDate.getMonth(), 1));
        }
    };

    const handleNext = () => {
        if (view === 'days') {
            setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
        } else {
            setCurrentDate(new Date(currentDate.getFullYear() + 1, currentDate.getMonth(), 1));
        }
    };

    const handleClear = (e) => {
        e.stopPropagation(); 
        onChange('');
        setIsOpen(false);
        setView('days');
    };

    // --- ЛОГІКА БЛОКУВАННЯ ---
    
    const isDayDisabled = (dateObj) => {
        if (minDate) {
            const min = parseDateToUTC(minDate);
            if (min && dateObj < min) return true;
        }
        if (maxDate) {
            const max = parseDateToUTC(maxDate);
            if (max && dateObj > max) return true;
        }
        return false;
    };

    const isMonthDisabled = (checkYear, checkMonth) => {
        if (minDate) {
            const lastDay = new Date(Date.UTC(checkYear, checkMonth + 1, 0));
            const min = parseDateToUTC(minDate);
            if (min && lastDay < min) return true;
        }
        if (maxDate) {
            const firstDay = new Date(Date.UTC(checkYear, checkMonth, 1));
            const max = parseDateToUTC(maxDate);
            if (max && firstDay > max) return true;
        }
        return false;
    };

    const isPrevDisabled = () => {
        if (!minDate) return false;
        const min = parseDateToUTC(minDate);
        if (view === 'days') {
            const lastDayOfPrevMonth = new Date(Date.UTC(currentDate.getFullYear(), currentDate.getMonth(), 0));
            return lastDayOfPrevMonth < min;
        } else {
            const lastDayOfPrevYear = new Date(Date.UTC(currentDate.getFullYear(), 0, 0));
            return lastDayOfPrevYear < min;
        }
    };

    const isNextDisabled = () => {
        if (!maxDate) return false;
        const max = parseDateToUTC(maxDate);
        if (view === 'days') {
            const firstDayOfNextMonth = new Date(Date.UTC(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
            return firstDayOfNextMonth > max;
        } else {
            const firstDayOfNextYear = new Date(Date.UTC(currentDate.getFullYear() + 1, 0, 1));
            return firstDayOfNextYear > max;
        }
    };

    // -------------------------

    const handleDayClick = (dayObj) => {
        if (isDayDisabled(dayObj.date)) return;

        if (dayObj.isPrevMonth) setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
        if (dayObj.isNextMonth) setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));

        const y = dayObj.date.getUTCFullYear();
        const m = String(dayObj.date.getUTCMonth() + 1).padStart(2, '0');
        const d = String(dayObj.date.getUTCDate()).padStart(2, '0');
        
        onChange(`${y}-${m}-${d}`);
        setIsOpen(false);
        setView('days');
    };

    const handleMonthClick = (monthIndex) => {
        if (isMonthDisabled(currentDate.getFullYear(), monthIndex)) return;
        setCurrentDate(new Date(currentDate.getFullYear(), monthIndex, 1));
        setView('days');
    };

    const displayValue = value ? value.split('-').reverse().join('.') : '';

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const prevMonthDays = getDaysInMonth(year, month - 1);

    const calendarDays = [];

    for (let i = 0; i < firstDay; i++) {
        const dayNum = prevMonthDays - firstDay + i + 1;
        calendarDays.push({
            dayNum,
            isPrevMonth: true,
            isNextMonth: false,
            date: new Date(Date.UTC(year, month - 1, dayNum))
        });
    }

    for (let i = 1; i <= daysInMonth; i++) {
        calendarDays.push({
            dayNum: i,
            isPrevMonth: false,
            isNextMonth: false,
            date: new Date(Date.UTC(year, month, i))
        });
    }

    const remainingCells = 42 - calendarDays.length;
    for (let i = 1; i <= remainingCells; i++) {
        calendarDays.push({
            dayNum: i,
            isPrevMonth: false,
            isNextMonth: true,
            date: new Date(Date.UTC(year, month + 1, i))
        });
    }

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
                        <button type="button" onClick={handlePrev} disabled={isPrevDisabled()}>‹</button>
                        <span 
                            className="custom-datepicker-title"
                            onClick={() => setView(view === 'days' ? 'months' : 'days')}
                        >
                            {view === 'days' ? `${MONTHS[month]} ${year}` : year}
                        </span>
                        <button type="button" onClick={handleNext} disabled={isNextDisabled()}>›</button>
                    </div>
                    
                    {view === 'days' ? (
                        <div className="custom-datepicker-grid">
                            {DAYS.map(day => (
                                <div key={day} className="custom-datepicker-day-name">{day}</div>
                            ))}
                            
                            {calendarDays.map((dayObj, index) => {
                                const y = dayObj.date.getUTCFullYear();
                                const m = String(dayObj.date.getUTCMonth() + 1).padStart(2, '0');
                                const d = String(dayObj.date.getUTCDate()).padStart(2, '0');
                                const dateString = `${y}-${m}-${d}`;
                                
                                const isSelected = value === dateString;
                                const disabled = isDayDisabled(dayObj.date);
                                const isOutside = dayObj.isPrevMonth || dayObj.isNextMonth;
                                
                                return (
                                    <div 
                                        key={index} 
                                        className={`custom-datepicker-day ${isSelected ? 'selected' : ''} ${disabled ? 'disabled' : ''} ${isOutside ? 'outside-month' : ''}`}
                                        onClick={() => !disabled && handleDayClick(dayObj)}
                                    >
                                        {dayObj.dayNum}
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="custom-datepicker-months-grid">
                            {SHORT_MONTHS.map((m, index) => {
                                const isSelected = index === month;
                                const disabled = isMonthDisabled(year, index);
                                
                                return (
                                    <div 
                                        key={m} 
                                        className={`custom-datepicker-month-item ${isSelected ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
                                        onClick={() => !disabled && handleMonthClick(index)}
                                    >
                                        {m}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default CustomDatePicker;