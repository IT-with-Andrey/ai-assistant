

import sys 

import os 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))



from backend.app.database.connection import SessionLocal , engine

from backend.app.database.models import Base , Message

from backend.app.services.assistant_service import chat

from backend.app.core.logger import logger

def main():
    logger.info("Запуск CLI-assistant")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        while True:
            user_input = input('You:')
            if user_input == 'exit':
                break
            logger.debug('Получен ввод от пользователя ')
            answer = chat(user_input, db)
            print(f'AI: {answer}')
    finally:
        db.commit()
        db.close()
        logger.info("Ceccя BD Успешно закрыта , выход из CLI")

if __name__ =="__main__":
    main()