import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

const LOADING_PHRASES = [
  'Анализ текста',
  'Думание',
  'Анализирую',
  'Думаю',
  'Готовлю',
  'Уже готово',
  'Подождите секундочку',
];

function App() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [provider, setProvider] = useState('ollama');
  const [sessionId] = useState(() => localStorage.getItem('session_id') || crypto.randomUUID());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingPhrase, setLoadingPhrase] = useState(LOADING_PHRASES[0]);
  const [showActionsIndex, setShowActionsIndex] = useState(null);

  const chatEndRef = useRef(null);
  const streamReaderRef = useRef(null);
  const loadingIntervalRef = useRef(null);

  const personas = [
    { id: 'default', name: 'Универсальный помощник' },
    { id: 'python_teacher', name: '🐍 Python Наставник' },
    { id: 'fitness_trainer', name: '💪 Фитнес-тренер' },
    { id: 'english_teacher', name: '🇬🇧 Учитель Английского' },
  ];

  const activeChat = chats.find(c => c.id === activeChatId) || null;
  const messages = activeChat?.messages || [];

  useEffect(() => {
    localStorage.setItem('session_id', sessionId);
  }, [sessionId]);

  // Смена фраз лоадера + очистка
  useEffect(() => {
    if (isLoading) {
      let idx = 0;
      loadingIntervalRef.current = setInterval(() => {
        idx = Math.floor(Math.random() * LOADING_PHRASES.length);
        setLoadingPhrase(LOADING_PHRASES[idx]);
      }, 1500);
    } else {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
    }
    return () => {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
      }
    };
  }, [isLoading]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const createChat = async (personaId) => {
    const newChat = {
      id: Date.now().toString(),
      personaId,
      personaName: personas.find(p => p.id === personaId)?.name || '',
      messages: [],
    };
    setChats(prev => [newChat, ...prev]);
    setActiveChatId(newChat.id);
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/chats/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, persona_id: personaId }),
      });
      const data = await res.json();
      if (data.provider) setProvider(data.provider);
      setChats(prev => prev.map(c =>
        c.id === newChat.id
          ? { ...c, messages: [...c.messages, { text: data.welcome_message, sender: 'assistant' }] }
          : c
      ));
    } catch (e) {
      setChats(prev => prev.map(c =>
        c.id === newChat.id
          ? { ...c, messages: [...c.messages, { text: 'Ошибка при инициализации чата', sender: 'assistant' }] }
          : c
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const stopStream = () => {
    if (streamReaderRef.current) {
      streamReaderRef.current.cancel();
      streamReaderRef.current = null;
    }
    setIsLoading(false);
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || isLoading || !activeChatId) return;
    const userMessage = messageText.trim();
    setInputValue('');

    setChats(prev => prev.map(c =>
      c.id === activeChatId
        ? { ...c, messages: [...c.messages, { text: userMessage, sender: 'user' }] }
        : c
    ));

    setIsLoading(true);

    setChats(prev => prev.map(c =>
      c.id === activeChatId
        ? { ...c, messages: [...c.messages, { text: '', sender: 'assistant' }] }
        : c
    ));

    try {
      const controller = new AbortController();
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          user_id: sessionId,
          persona_id: activeChat.personaId,
        }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);

      const reader = response.body.getReader();
      streamReaderRef.current = reader;
      const decoder = new TextDecoder();
      let assistantText = '';
      let shouldStop = false;

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
              shouldStop = true;
              controller.abort();
              break;
            }
            assistantText += token;
            setChats(prev => prev.map(c => {
              if (c.id !== activeChatId) return c;
              const updatedMessages = [...c.messages];
              const lastIdx = updatedMessages.length - 1;
              if (lastIdx >= 0 && updatedMessages[lastIdx].sender === 'assistant') {
                updatedMessages[lastIdx] = { text: assistantText, sender: 'assistant' };
              }
              return { ...c, messages: updatedMessages };
            }));
          }
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Ошибка при стриме:', error);
        setChats(prev => prev.map(c => {
          if (c.id !== activeChatId) return c;
          const updatedMessages = [...c.messages];
          const lastIdx = updatedMessages.length - 1;
          if (lastIdx >= 0 && updatedMessages[lastIdx].sender === 'assistant') {
            updatedMessages[lastIdx] = { text: 'Извините, ошибка соединения.', sender: 'assistant' };
          }
          return { ...c, messages: updatedMessages };
        }));
      }
    } finally {
      streamReaderRef.current = null;
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleNewChat = () => {
    stopStream();
    setActiveChatId(null);
    setProvider('ollama');
  };

  const switchToChat = (chatId) => {
    if (chatId === activeChatId) return;
    stopStream();
    setActiveChatId(chatId);
    setProvider('ollama');
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).catch(err => console.error('Copy failed:', err));
    // Можно добавить кратковременную индикацию, но пока просто копируем
  };

  const currentPersonaName = activeChat?.personaName || '';

  return (
    <div className="app-wrapper">
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-top">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" /><line x1="9" y1="3" x2="9" y2="21" />
            </svg>
          </button>
          <div className="logo">Прототип</div>
        </div>
        <button className="new-chat-btn" onClick={handleNewChat}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Новый чат
        </button>
        <div className="sidebar-search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input type="text" placeholder="Поиск чатов" disabled />
        </div>
        <div className="sidebar-section">
          <div className="sidebar-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
            Images
          </div>
          <div className="sidebar-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            Library
          </div>
        </div>
        <div className="sidebar-section recents">
          <div className="section-header">Recents</div>
          <div className="recent-list">
            {chats.filter(c => c.messages.length > 1).length === 0 ? (
              <div className="empty-recents">Нет истории чатов</div>
            ) : (
              chats.filter(c => c.messages.length > 1).map(chat => (
                <div
                  key={chat.id}
                  className={`recent-item ${chat.id === activeChatId ? 'active' : ''}`}
                  onClick={() => switchToChat(chat.id)}
                >
                  <span className="recent-title">
                    {chat.messages.find(m => m.sender === 'user')?.text || 'Новый чат'}
                  </span>
                  <span className="recent-role">{chat.personaName}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>

      <main className="main-content">
        <div className="top-actions">
          <button className="upgrade-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            Upgrade
          </button>
          <div className="user-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v1.2h19.2v-1.2c0-3.2-6.4-4.8-9.6-4.8z" />
            </svg>
          </div>
          <span className={`provider-badge ${provider === 'ollama' ? 'ollama' : 'gemini'}`}>
            {provider === 'ollama' ? '🟢 Ollama' : '🔵 Gemini'}
          </span>
        </div>

        <div className="chat-area">
          {!activeChat ? (
            <div className="persona-select-screen">
              <h2>Выбери роль</h2>
              <div className="persona-buttons">
                {personas.map(p => (
                  <button key={p.id} className="persona-button" onClick={() => createChat(p.id)} disabled={isLoading}>
                    {p.name}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.length === 0 && (
                <div className="welcome-screen">
                  <h1 className="welcome-text">Привет, User, чем займемся?</h1>
                  <div className="role-plate inline-role">
                    <span>Роль: {currentPersonaName}</span>
                  </div>
                </div>
              )}

              <div className="chat-messages">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`message-wrapper ${msg.sender === 'user' ? 'user-row' : 'assistant-row'}`}
                    onMouseEnter={() => msg.sender === 'assistant' && setShowActionsIndex(index)}
                    onMouseLeave={() => setShowActionsIndex(null)}
                  >
                    {msg.sender === 'user' ? (
                      <div className="user-capsule">{msg.text}</div>
                    ) : (
                      <>
                        <div className="assistant-text">
                          <ReactMarkdown>{msg.text.replace(/\n/g, '  \n')}</ReactMarkdown>
                        </div>
                        <div className={`actions-bar ${showActionsIndex === index ? 'visible' : ''}`}>
                          <button className="action-icon" title="Нравится">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                          </button>
                          <button className="action-icon" title="Не нравится">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
                          </button>
                          <button className="action-icon" title="Перегенерировать">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                          </button>
                          <button className="action-icon" title="Копировать" onClick={() => copyToClipboard(msg.text)}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                          </button>
                          <button className="action-icon" title="Меню">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}

                {isLoading && (
                  <div className="message-wrapper assistant-row">
                    <div className="loading-text">{loadingPhrase}</div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="input-area">
                <form className="chat-input-form" onSubmit={handleSubmit}>
                  <button type="button" className="attach-btn" aria-label="Прикрепить">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                    </svg>
                  </button>
                  <input
                    type="text"
                    placeholder="Ask Прототип"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    autoFocus
                  />
                  <div className="input-right-tools">
                    <button type="button" className="model-selector" disabled>
                      Flash v
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="6 9 12 15 18 9" />
                      </svg>
                    </button>
                    <button type="button" className="mic-btn" aria-label="Голосовой ввод">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                        <line x1="12" y1="19" x2="12" y2="23" />
                        <line x1="8" y1="23" x2="16" y2="23" />
                      </svg>
                    </button>
                    {isLoading ? (
                      <button type="button" className="stop-btn" onClick={stopStream} aria-label="Остановить генерацию">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <rect x="4" y="4" width="16" height="16" rx="2" />
                        </svg>
                      </button>
                    ) : (
                      <button type="submit" className="send-btn" disabled={!inputValue.trim() || isLoading}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                          <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
                        </svg>
                      </button>
                    )}
                  </div>
                </form>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;