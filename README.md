AI Assistant — Project Architecture (README)
📌 Project Idea

Personal AI assistant for:

learning programming
tracking progress
storing memory/history
helping with code
working with local or cloud LLMs

The project is built progressively in stages:

simple working core first
then memory
then database
then API
then tools/features

Main goal:

build a real middle-level backend project instead of a simple pet-project script.

🧠 Main Philosophy

The AI model is replaceable.

The real system is:

architecture
memory
context management
backend logic
database
tools
state management

Models can be swapped:

OpenAI
OpenRouter
Ollama
LM Studio
local LLaMA
Claude
DeepSeek

without rewriting the whole project.

🏗 Project Architecture
User
 ↓
Application Layer
 ↓
Assistant Core
 ↓
Memory System
 ↓
Database
 ↓
LLM Provider
 ↓
AI Response
📂 Project Structure
ai-assistant/
│
├── app/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── settings.py
│   │   └── logger.py
│   │
│   ├── ai/
│   │   ├── provider.py
│   │   ├── prompts.py
│   │   ├── memory_manager.py
│   │   └── context_builder.py
│   │
│   ├── services/
│   │   ├── assistant_service.py
│   │   └── chat_service.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── repositories/
│   │
│   ├── api/
│   │   ├── routes/
│   │   └── dependencies.py
│   │
│   ├── schemas/
│   │   ├── chat.py
│   │   └── user.py
│   │
│   ├── tools/
│   │   ├── file_tool.py
│   │   ├── search_tool.py
│   │   └── code_tool.py
│   │
│   └── main.py
│
├── tests/
│
├── requirements.txt
├── .env
├── README.md
└── docker-compose.yml
⚙️ Tech Stack
Backend
Python
FastAPI
Database
PostgreSQL
ORM
SQLAlchemy 2.0
AI Providers
OpenRouter
OpenAI
Ollama
LM Studio
Async
asyncio
httpx
DevOps
Docker