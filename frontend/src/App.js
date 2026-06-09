// src/App.js
import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (text, sender) => {
    setMessages(prev => [...prev, { text, sender }]);
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage = messageText.trim();
    addMessage(userMessage, 'user');
    setInputValue('');
    setIsLoading(true);

    // Добавляем пустое сообщение ассистента, которое будем заполнять
    addMessage('', 'assistant');

    try {
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, user_id: 'default_user' }),
      });

      if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantText = '';
      let shouldStop = false; // Флаг для выхода из WHILE

      while (!shouldStop) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const token = line.slice(6);
            
            if (token.startsWith('[ERROR]')) {
              assistantText += '\n[Ошибка: ' + token.replace('[ERROR]', '').trim() + ']';
              shouldStop = true; // Сигнализируем о выходе из while
              await reader.cancel(); // Явно говорим браузеру закрыть поток
              break; // Выходим из for
            }
            
            assistantText += token;
            
            // Обновляем именно сообщение ассистента
            setMessages(prev => {
              const updated = [...prev];
              const lastIdx = updated.length - 1;
              if (lastIdx >= 0 && updated[lastIdx].sender === 'assistant') {
                updated[lastIdx] = { text: assistantText, sender: 'assistant' };
              }
              return updated;
            });
          }
        }
      }
    } catch (error) {
      console.error('Ошибка при стриме:', error);
      setMessages(prev => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        if (lastIdx >= 0 && updated[lastIdx].sender === 'assistant') {
          updated[lastIdx] = { text: 'Извините, ошибка соединения.', sender: 'assistant' };
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleTestFacts = async () => {
    if (isLoading) return;
    const userMessage = '/test';
    addMessage(userMessage, 'user');
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });
      if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);
      const data = await response.json();
      addMessage(data.response, 'assistant');
    } catch (error) {
      addMessage('Ошибка загрузки тестовых фактов.', 'assistant');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Prototype</h1>
        <button
          className="test-facts-button"
          onClick={handleTestFacts}
          disabled={isLoading}
        >
          Загрузить тестовые факты
        </button>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-chat">
            <p>Чем я могу помочь?</p>
          </div>
        )}
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.sender === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-bubble">
              {msg.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant-message">
            <div className="message-bubble typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Введите сообщение..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isLoading}
          autoFocus
        />
        <button type="submit" disabled={isLoading || !inputValue.trim()}>
          Отправить
        </button>
      </form>
    </div>
  );
}

export default App;