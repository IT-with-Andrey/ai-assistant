import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.app.database.connection import SessionLocal, engine, Base
from backend.app.database.models import Message, Summary
from backend.app.services.assistant_service import chat
from backend.app.core.logger import logger

def auto_test_memory(db):
    """Молча загружает тестовые факты и сразу спрашивает 'Что ты знаешь обо мне?'"""
    test_phrases = [
        "Привет! Меня зовут Андрей.",
        "Я живу в городе на реке Рейн.",
        "Моё хобби — программирование на Python.",
        "Я хочу выучить английский язык.",
        "Моя цель — создать свою AI-компанию.",
        "Я люблю работать с FastAPI.",
        "Мне нравится чистая архитектура кода.",
        "Я предпочитаю общаться с людьми.",
        "Мой главный принцип — энтузиазм.",
        "Я люблю жизнь и технологии."
    ]
    logger.info("Автоматическая загрузка 10 тестовых фактов...")
    for msg in test_phrases:
        _ = chat(msg, db)  # молча загружаем факты
    logger.info("Загрузка завершена. Запрашиваю финальный ответ...")
    final_answer = chat("Что ты знаешь обо мне?", db)
    print(f"AI: {final_answer}")

def main():
    logger.info('"Запуск CLI-ассистента"')
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        while 1:
            
            user_input = input('You: ')
            if user_input == 'exit':
                break
            if user_input == '/test':
                auto_test_memory(db)
                continue
            logger.debug("Получен ввод пользователя")
            answer = chat(user_input, db)
            print(f'AI: {answer}')
    finally:
        db.commit()
        db.close()
        logger.info("Сессия БД закрыта, выход из CLI")

if __name__ == '__main__':
    main()
