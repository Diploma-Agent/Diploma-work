import React, { useState, useRef, useEffect } from 'react';
import '../styles/chatStyles.css';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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
        } else if (line.match(/^[\*\-•]\s/)) {
            listBuffer.push(<li key={i}>{formatInline(line.replace(/^[\*\-•]\s/, ''))}</li>);
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

function ChatComponent() {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [messages, setMessages] = useState([
        { id: 1, text: 'Привіт! Я ваш фінансовий помічник. Чим можу допомогти?', sender: 'bot', agent: 'Фінансовий Асистент 🤖' }
    ]);
    const [inputText, setInputText] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [error, setError] = useState(null);
    const messagesEndRef = useRef(null);

    const toggleChat = () => setIsOpen(!isOpen);
    const toggleExpand = () => setIsExpanded(!isExpanded);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

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
            const token = localStorage.getItem('access_token')
                || localStorage.getItem('token')
                || localStorage.getItem('accessToken')
                || sessionStorage.getItem('access_token');

            if (!token) throw new Error('Не авторизовано. Будь ласка, увійдіть в систему.');

            // Передаємо історію (без першого привітання бота)
            const history = updatedMessages.slice(1, -1).map(msg => ({
                role: msg.sender === 'user' ? 'user' : 'model',
                text: msg.text
            }));

            const { data } = await axios.post(
                `${API_URL}/finance/ai/chat/`,
                { message: inputText, history },
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
                <div className={`chat-window ${isExpanded ? 'chat-window--expanded' : ''}`}>
                    <div className="chat-header">
                        <div className="chat-title">
                            <span>🤖</span> Фінансовий помічник
                        </div>
                        <div className="chat-header-actions">
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
