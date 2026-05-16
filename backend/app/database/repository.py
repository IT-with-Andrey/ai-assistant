

from backend.app.database.connenction import SessionLocal
from backend.app.database.models import Message


def save_message(role: str , content: str):
    db = SessionLocal()

    msg = Message(role=role, content=content)


    db.add(msg)
    db.commit()
    db.close()

def  get_last_messages(limit: int=10):
    db = SessionLocal()

    messages = db.query(Message)\
            .order_by(Message.id.desc())\
            .limit(limit)\
            .all()
    db.close()

    return list(reversed(messages))
