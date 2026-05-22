from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database.connection import Base, engine
from backend.app.database import models
from backend.app.services.assistant_service import chat as assistant_chat
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.services.cli import auto_test_memory

app = FastAPI()


Base.metadata.create_all(bind=engine)


origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get('/health')
def health():
    return {'server': 'running'}



@app.post("/chat")
def chat(data: dict, db: Session = Depends(get_db)):
    msg = data.get('message')

    # --- Обработка специальной команды /test ---
    if msg == '/test':
        auto_test_memory(db)
        return {
            "response": "Тестовые факты загружены. Теперь спросите: Что ты знаешь обо мне?",
            "original": msg
        }

    # --- Стандартная проверка сообщения ---
    if msg is None or msg.strip() == "":
        return {"error": "Сообщение не может быть пустым или состоять из одних пробелов"}
    if len(msg) > 2000:   # лимит увеличен до 2000 символов
        return {'error': 'Сообщение слишком длинное (максимум 2000 символов)'}

    # --- Отправляем сообщение ассистенту ---
    response = assistant_chat(msg, db)
    return {
        "response": response,
        "original": msg
    }