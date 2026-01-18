import React, { useState, useRef, useEffect } from 'react';
import '../styles/chatStyles.css';

function ChatComponent() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { id: 1, text: 'Привіт! Я ваш фінансовий помічник. Чим можу допомогти?', sender: 'bot' }
    ]);
    const [inputText, setInputText] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const toggleChat = () => {
        setIsOpen(!isOpen);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputText.trim()) return;

        const userMessage = {
            id: Date.now(),
            text: inputText,
            sender: 'user'
        };

        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsTyping(true);

        // Simulate API call / delayed response
        setTimeout(() => {
            const botResponse = generateResponse(inputText);
            const botMessage = {
                id: Date.now() + 1,
                text: botResponse,
                sender: 'bot'
            };
            setMessages(prev => [...prev, botMessage]);
            setIsTyping(false);
        }, 1500);
    };

    // Simple mock response generator - in a real app this would call an API
    const generateResponse = (text) => {
        const lowerText = text.toLowerCase();
        
        if (lowerText.includes('баланс') || lowerText.includes('грош')) {
            return 'Ви можете переглянути детальний баланс на сторінці Дашборд або Аналітика.';
        }
        if (lowerText.includes('інвест')) {
            return 'Для інвестування рекомендуємо розглянути диверсифікований портфель. Загляньте в розділ Аналітика для персональних рекомендацій.';
        }
        if (lowerText.includes('біткоїн') || lowerText.includes('crypto') || lowerText.includes('крипт')) {
            return 'Ринок криптовалют волатильний. Перевірте поточні курси на сторінці Транзакцій або додайте біржу в Профілі.';
        }
        if (lowerText.includes('привіт')) {
            return 'Вітаю! Готовий допомогти з вашими фінансами.';
        }
        
        return 'Я поки навчаюсь і не можу відповісти на це питання точно. Спробуйте запитати про баланс, інвестиції або транзакції.';
    };

    return (
        <div className="chat-widget-container">
            {isOpen ? (
                <div className="chat-window">
                    <div className="chat-header">
                        <div className="chat-title">
                            <span>🤖</span> Фінансовий помічник
                        </div>
                        <button className="close-btn" onClick={toggleChat}>×</button>
                    </div>
                    
                    <div className="chat-messages">
                        {messages.map(msg => (
                            <div key={msg.id} className={`message ${msg.sender}`}>
                                {msg.text}
                            </div>
                        ))}
                        {isTyping && (
                            <div className="typing-indicator">
                                Друкує...
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <form className="chat-input-area" onSubmit={handleSendMessage}>
                        <input
                            type="text"
                            className="chat-input"
                            placeholder="Запитайте про фінанси..."
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                        />
                        <button type="submit" className="send-btn" disabled={!inputText.trim()}>
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
