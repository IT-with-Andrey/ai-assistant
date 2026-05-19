
backend/
├── core/
│   └── config.py              ← читает .env, отдаёт API_KEY и MODEL
│
├── database/
│   ├── connection.py          ← engine, SessionLocal, Base, get_db()
│   ├── models.py              ← описание таблицы Message
│   └── repository.py          ← save_message(), get_last_messages() (чистые операции с БД)
│
├── ai/
│   ├── prompts.py             ← SYSTEM_PROMPT (личность ассистента)
│   ├── context_builder.py     ← build_context() – собирает history + system + user
│   └── provider.py            ← generate_response() – запрос к LLM (Ollama / OpenRouter)
│
└── services/
    ├── assistant_service.py   ← chat() – ГЛАВНЫЙ ОРКЕСТРАТОР (связывает все части)
    ├── cli.py                 ← терминальный интерфейс (бесконечный цикл "You: / AI:")
    └── main.py                ← FastAPI-сервер (POST /chat)

 
Пользователь (терминал)
   │
   ▼
cli.py:
   db = SessionLocal()                 ──┐
   user_input = input("You: ")          │
   answer = chat(user_input, db) ──┐    │
   print(f"AI: {answer}")          │    │
   db.close()                      │    │
                                   │    │
                                   ▼    │
assistant_service.py: chat()      │    │
   │                               │    │
   ├─ save_message(db, 'user', user_input)  ────► repository.py → Message → БД
   │
   ├─ history_msgs = get_last_messages(db, 10) ─► repository.py → БД
   │
   ├─ history = [{role, content}, ...]  (преобразование объектов в словари)
   │
   ├─ messages = build_context(history, user_input) ──► context_builder.py
   │      │                                                │
   │      │  ┌─ system: SYSTEM_PROMPT  ◄─── prompts.py
   │      │  ├─ ...старые сообщения...
   │      │  └─ user: user_input
   │      │
   │      ▼
   ├─ answer = generate_response(messages) ──► provider.py
   │      │                                       │
   │      │  ┌─ Ollama (localhost:11434)
   │      │  └─ или OpenRouter API
   │      │
   │      ▼  (возвращает текст)
   │
   ├─ save_message(db, 'assistant', answer)  ──► repository.py → БД
   │
   └─ return answer

 Пользователь (CLI / FastAPI)
   │  "Привет"
   ▼
run_cli.py / main.py
   │  user_input
   ▼
assistant_service.chat(user_input, db)
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  1. Сохраняем сообщение пользователя                         │
│  │     save_message(db, role='user', content=user_input)       │
│  │     → repository.py                                         │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  2. Получаем историю (последние 10 сообщений)                │
│  │     message_from_db = get_last_messages(db, limit=10)       │
│  │     → repository.py                                         │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  3. Если >= MAX_HISTORY (10):                               │
│  │     • old_messages = message_from_db[:6]                    │
│  │     • summary_prompt = [system + склеенные старые сообщ.]   │
│  │     • summary_text = generate_response(summary_prompt)      │
│  │       → provider.py (HTTP POST на Ollama)                  │
│  │     • save_summary(db, summary_text)                        │
│  │       → repository.py                                       │
│  │     • DELETE old_messages из Message                        │
│  │       → прямой SQL через db.execute(delete(...))            │
│  │     • обновляем message_from_db                             │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  4. Конвертируем Message-объекты в список словарей          │
│  │     history = [{'role':..., 'content':...}, ...]           │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  5. Берём последнюю сохранённую сводку                       │
│  │     latest_summary = get_lastest_summary(db)                │
│  │     → repository.py                                         │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  6. Собираем контекст для LLM                                │
│  │     context_message = build_context(                         │
│  │         history, user_input,                                │
│  │         summary=latest_summary.content if latest_summary    │
│  │         else None                                           │
│  │     )                                                        │
│  │     → context_builder.py                                    │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  7. Генерируем ответ ассистента                              │
│  │     answer = generate_response(context_message)             │
│  │     → provider.py (HTTP POST на Ollama)                    │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  8. Сохраняем ответ ассистента                               │
│  │     save_message(db, role='assistant', content=answer)      │
│  │     → repository.py                                         │
│  └─────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────┐
│  │  9. Возвращаем ответ пользователю                            │
│  │     return answer                                           │
│  └─────────────────────────────────────────────────────────────┘

Итог: пользователь видит "Привет! Чем могу помочь?"


Short-term memory
↓
Summarization memory
↓
Vector/RAG memory
↓
User profile memory
↓
Tool memory / episodic memory
↓
Knowledge base