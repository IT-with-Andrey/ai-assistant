
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

   ┌─────────────────────────────────────────────┐
│                  USER                       │
│  Пишет сообщение: "Привет"                 │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│               INTERFACE LAYER               │
│                                             │
│  cli.py            или        main.py       │
│  (терминал)                   (FastAPI)     │
│                                             │
│  Получает сообщение пользователя            │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│            assistant_service.py             │
│                                             │
│         ГЛАВНЫЙ ОРКЕСТРАТОР СИСТЕМЫ         │
│                                             │
│  chat(user_message)                         │
│                                             │
│  1. сохраняет user message                  │
│  2. достаёт history                         │
│  3. собирает context                        │
│  4. вызывает LLM                            │
│  5. сохраняет ответ AI                      │
│  6. возвращает ответ                        │
└─────────────────────────────────────────────┘
         │                  │
         │                  │
         ▼                  ▼

┌───────────────────┐    ┌────────────────────┐
│    DATABASE       │    │      AI LAYER      │
└───────────────────┘    └────────────────────┘
         │                          │
         ▼                          ▼

┌───────────────────┐    ┌────────────────────┐
│  repository.py    │    │ context_builder.py │
│                   │    │                    │
│ save_message()    │    │ build_context()    │
│ get_history()     │    │                    │
│                   │    │ Собирает:          │
│ Чистая работа     │    │                    │
│ с базой данных    │    │ - system prompt    │
│                   │    │ - history          │
│                   │    │ - user message     │
└───────────────────┘    └────────────────────┘
         │                          │
         ▼                          ▼

┌───────────────────┐    ┌────────────────────┐
│    models.py      │    │    prompts.py      │
│                   │    │                    │
│ Message table     │    │ SYSTEM_PROMPT      │
│                   │    │                    │
│ id                │    │ "Ты AI assistant"  │
│ role              │    │                    │
│ content           │    │ Характер модели    │
│ timestamp         │    │ Правила поведения  │
└───────────────────┘    └────────────────────┘
         │
         ▼
┌───────────────────┐
│ connection.py     │
│                   │
│ engine            │
│ SessionLocal      │
│ Base              │
│ get_db()          │
│                   │
│ Подключение       │
│ к PostgreSQL      │
└───────────────────┘


                     ▼
┌─────────────────────────────────────────────┐
│               provider.py                   │
│                                             │
│        generate_response(messages)          │
│                                             │
│  Универсальный адаптер к LLM                │
│                                             │
│  Может работать с:                          │
│  - Ollama                                   │
│  - OpenAI                                   │
│  - Claude                                   │
│  - OpenRouter                               │
│                                             │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│                  LLM MODEL                  │
│                                             │
│  llama3 / mistral / gpt-4 / claude          │
│                                             │
│  Получает context                           │
│  Генерирует ответ                           │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              AI RESPONSE                    │
│                                             │
│ "Привет! Чем могу помочь?"                  │