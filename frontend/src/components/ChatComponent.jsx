import React, { useState, useRef, useEffect } from 'react';
import '../styles/chatStyles.css';
import axios from 'axios';

// Відносний /api → Vite proxy локально, Django напряму в контейнері
const API_URL = `${import.meta.env.VITE_API_BASE_URL || ''}/api`;

const formatMessage = (text) => {
    const lines = text.split('\n');
    const result = [];
    let listBuffer = [];

    const flushList = () => {
        if (listBuffer.length > 0) {
            result.push(<ul key={`list-${result.length}`} className="msg-list">{listBuffer}</ul>);
            listBuffer = [];
        }
    };

    lines.forEach((line, i) => {
        if (line.startsWith('### ')) {
            flushList();
            result.push(<h5 key={i} className="msg-h3">{formatInline(line.replace('### ', ''))}</h5>);
        } else if (line.startsWith('## ')) {
            flushList();
            result.push(<h4 key={i} className="msg-h2">{formatInline(line.replace('## ', ''))}</h4>);
        } else if (line.startsWith('# ')) {
            flushList();
            result.push(<h3 key={i} className="msg-h1">{formatInline(line.replace('# ', ''))}</h3>);
        } else if (line.match(/^[-*•]\s/)) {
            listBuffer.push(<li key={i}>{formatInline(line.replace(/^[-*•]\s/, ''))}</li>);
        } else if (line.match(/^\d+\.\s/)) {
            listBuffer.push(<li key={i}>{formatInline(line.replace(/^\d+\.\s/, ''))}</li>);
        } else if (line.trim() === '') {
            flushList();
            result.push(<div key={i} className="msg-spacer" />);
        } else {
            flushList();
            result.push(<p key={i} className="msg-p">{formatInline(line)}</p>);
        }
    });

    flushList();
    return result;
};

const formatInline = (text) => {
    // Підтримка **bold**, *italic*, `code`, ==highlight==
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`|==.*?==)/g);
    return parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**'))
            return <strong key={i} className="msg-bold">{part.slice(2, -2)}</strong>;
        if (part.startsWith('*') && part.endsWith('*'))
            return <em key={i} className="msg-italic">{part.slice(1, -1)}</em>;
        if (part.startsWith('`') && part.endsWith('`'))
            return <code key={i} className="msg-code">{part.slice(1, -1)}</code>;
        if (part.startsWith('==') && part.endsWith('=='))
            return <mark key={i} className="msg-highlight">{part.slice(2, -2)}</mark>;
        return part;
    });
};

const WELCOME_MSG = { id: 'welcome', text: 'Привіт! Я ваш фінансовий помічник. Чим можу допомогти?', sender: 'bot', agent: 'Фінансовий Асистент 🤖' };

function ChatComponent() {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [chatPosition, setChatPosition] = useState(null);
    const [messages, setMessages] = useState([WELCOME_MSG]);
    const [inputText, setInputText] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [historyLoaded, setHistoryLoaded] = useState(false);
    const [error, setError] = useState(null);
    const messagesEndRef = useRef(null);
    const chatWindowRef = useRef(null);
    const dragOffsetRef = useRef({ x: 0, y: 0 });

    const getToken = () =>
        localStorage.getItem('access_token') ||
        localStorage.getItem('token') ||
        localStorage.getItem('accessToken') ||
        sessionStorage.getItem('access_token');

    // Завантажуємо збережену історію з бекенду при першому відкритті
    useEffect(() => {
        if (!isOpen || historyLoaded) return;

        const token = getToken();
        if (!token) { setHistoryLoaded(true); return; }

        axios.get(`${API_URL}/finance/ai/chat/history/`, {
            headers: { Authorization: `Bearer ${token}` }
        }).then(({ data }) => {
            const loaded = (data.history || []).map((msg, i) => ({
                id: `hist-${i}`,
                text: msg.text,
                sender: msg.role === 'user' ? 'user' : 'bot',
                agent: msg.agent || 'Фінансовий Асистент 🤖',
            }));
            if (loaded.length > 0) {
                setMessages([WELCOME_MSG, ...loaded]);
            }
        }).catch(() => {
            // Якщо не вдалося — просто залишаємо привітання
        }).finally(() => {
            setHistoryLoaded(true);
        });
    }, [isOpen]);

    const handleClearHistory = async () => {
        const token = getToken();
        if (!token) return;
        try {
            await axios.delete(`${API_URL}/finance/ai/chat/history/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setMessages([WELCOME_MSG]);
        } catch {
            // ігноруємо помилку
        }
    };

    const toggleChat = () => setIsOpen(!isOpen);
    const toggleExpand = () => setIsExpanded(!isExpanded);

    const clampPosition = (left, top) => {
        const chatEl = chatWindowRef.current;
        if (!chatEl) return { left, top };

        const maxLeft = Math.max(window.innerWidth - chatEl.offsetWidth, 0);
        const maxTop = Math.max(window.innerHeight - chatEl.offsetHeight, 0);

        return {
            left: Math.min(Math.max(left, 0), maxLeft),
            top: Math.min(Math.max(top, 0), maxTop)
        };
    };

    const handleHeaderPointerDown = (e) => {
        if (e.button !== undefined && e.button !== 0) return;
        if (e.target.closest('button')) return;

        const chatEl = chatWindowRef.current;
        if (!chatEl) return;

        const rect = chatEl.getBoundingClientRect();
        const nextLeft = chatPosition?.left ?? rect.left;
        const nextTop = chatPosition?.top ?? rect.top;

        dragOffsetRef.current = {
            x: e.clientX - nextLeft,
            y: e.clientY - nextTop,
        };

        setChatPosition({ left: nextLeft, top: nextTop });
        setIsDragging(true);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    useEffect(() => {
        if (!isDragging) return;

        const handlePointerMove = (e) => {
            const unclampedLeft = e.clientX - dragOffsetRef.current.x;
            const unclampedTop = e.clientY - dragOffsetRef.current.y;
            setChatPosition(clampPosition(unclampedLeft, unclampedTop));
        };

        const handlePointerUp = () => {
            setIsDragging(false);
        };

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);

        return () => {
            window.removeEventListener('pointermove', handlePointerMove);
            window.removeEventListener('pointerup', handlePointerUp);
        };
    }, [isDragging]);

    useEffect(() => {
        if (!chatPosition) return;

        const handleResize = () => {
            setChatPosition((prev) => {
                if (!prev) return prev;
                return clampPosition(prev.left, prev.top);
            });
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [chatPosition, isExpanded]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputText.trim() || isTyping) return;

        setError(null);
        const userMessage = { id: Date.now(), text: inputText, sender: 'user' };
        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);
        setInputText('');
        setIsTyping(true);

        try {
            const token = getToken();
            if (!token) throw new Error('Не авторизовано. Будь ласка, увійдіть в систему.');

            // Історія тепер зберігається на бекенді — передаємо лише нове повідомлення
            const { data } = await axios.post(
                `${API_URL}/finance/ai/chat/`,
                { message: inputText },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                text: data.response,
                sender: 'bot',
                agent: data.agent || 'Фінансовий Асистент 🤖'
            }]);
        } catch (err) {
            const errMsg = err.response?.data?.error || err.message || 'Не вдалося отримати відповідь.';
            setError(errMsg);
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                text: `⚠️ ${errMsg}`,
                sender: 'bot'
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="chat-widget-container">
            {isOpen ? (
                <div
                    ref={chatWindowRef}
                    className={`chat-window ${isExpanded ? 'chat-window--expanded' : ''} ${isDragging ? 'chat-window--dragging' : ''}`}
                    style={chatPosition ? { left: `${chatPosition.left}px`, top: `${chatPosition.top}px`, right: 'auto', bottom: 'auto' } : undefined}
                >
                    <div className="chat-header" onPointerDown={handleHeaderPointerDown}>
                        <div className="chat-title">
                            <span>🤖</span> Фінансовий помічник
                        </div>
                        <div className="chat-header-actions">
                            <button
                                className="expand-btn"
                                onClick={handleClearHistory}
                                title="Очистити історію чату"
                            >
                                🗑
                            </button>
                            <button
                                className="expand-btn"
                                onClick={toggleExpand}
                                title={isExpanded ? 'Зменшити' : 'Збільшити'}
                            >
                                {isExpanded ? '⊡' : '⊞'}
                            </button>
                            <button className="close-btn" onClick={toggleChat}>×</button>
                        </div>
                    </div>

                    <div className="chat-messages">
                        {messages.map(msg => (
                            <div key={msg.id} className={`message ${msg.sender}`}>
                                {msg.sender === 'bot' && (
                                    <div className="agent-label">{msg.agent}</div>
                                )}
                                {msg.sender === 'bot'
                                    ? <div className="message-content">{formatMessage(msg.text)}</div>
                                    : msg.text
                                }
                            </div>
                        ))}
                        {isTyping && (
                            <div className="typing-indicator">
                                <span></span><span></span><span></span>
                            </div>
                        )}
                        {error && <div className="chat-error">{error}</div>}
                        <div ref={messagesEndRef} />
                    </div>

                    <form className="chat-input-area" onSubmit={handleSendMessage}>
                        <input
                            type="text"
                            className="chat-input"
                            placeholder="Запитайте про фінанси..."
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            disabled={isTyping}
                        />
                        <button type="submit" className="send-btn" disabled={!inputText.trim() || isTyping}>
                            ➤
                        </button>
                    </form>
                </div>
            ) : (
                <button className="chat-toggle-btn" onClick={toggleChat}>
                    <div className="chat-icon">💬</div>
                </button>
            )}
        </div>
    );
}

export default ChatComponent;
