// src/App.js
import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [personaId, setPersonaId] = useState(null);   // выбранная роль
  const [personas] = useState([                         // список ролей
    { id: "default", name: "Универсальный помощник" },
    { id: "python_teacher", name: "🐍 Python Наставник" },
    { id: "fitness_trainer", name: "💪 Фитнес-тренер" },
    { id: "english_teacher", name: "🇬🇧 Учитель Английского" },
  ]);
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

  const selectPersona = async (id) => {
    setPersonaId(id);
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/chats/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: 'guest', persona_id: id })
      });
      const data = await res.json();
      addMessage(data.welcome_message, 'assistant');
    } catch (e) {
      addMessage('Ошибка при инициализации чата', 'assistant');
    } finally {
      setIsLoading(false);
    }
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
        body: JSON.stringify({ message: userMessage, user_id: 'guest', persona_id: personaId }),
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

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Prototype</h1>
      </header>

      <div className="chat-messages">
        {/* Кнопки выбора роли */}
        {!personaId && (
          <div className="persona-select">
            <h2>Выбери роль</h2>
            <div className="persona-buttons">
              {personas.map(p => (
                <button
                  key={p.id}
                  className="persona-button"
                  onClick={() => selectPersona(p.id)}
                  disabled={isLoading}
                >
                  {p.name}
                </button>
              ))}
            </div>
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

      {/* Форма ввода (активна только после выбора роли) */}
      {personaId && (
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
      )}
    </div>
  );
}

export default App;