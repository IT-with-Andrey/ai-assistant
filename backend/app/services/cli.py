from backend.app.database.connection import SessionLocal, engine, Base
from backend.app.database.models import Message, Summary
from backend.app.services.assistant_service import chat


def main():

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        while 1:
            user_input = input('You: ')
            if user_input == 'exit':
                break
            answer = chat(user_input, db)
            print(f'AI: {answer}')
    finally:
        db.commit()
        db.close()


if __name__ == '__main__':
    main()
