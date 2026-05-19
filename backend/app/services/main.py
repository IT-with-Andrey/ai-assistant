from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database.connection import Base, engine
from backend.app.database import models
from backend.app.services.assistant_service import chat as assistant_chat
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
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
def chat(data: dict , db: Session = Depends(get_db)):
    msg = data.get('message')

    

    # Проверка: если None или только пробелы -> ошибка
    if msg is None or msg.strip() == "":
        return {"error": "Сообщение не может быть пустым или состоять из одних пробелов"}
    if len(msg) > 30:
        return {'error': 'Слишком много жи есть да '}
    response = assistant_chat(msg,db)
    return {
        "response": response,
        "original": msg
        
    }
