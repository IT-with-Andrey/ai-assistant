


from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.database.models import Message


def save_message(db: Session , role: str , content:str) -> Message:
    new_message = Message(role=role , content=content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def get_last_messages(db: Session, limit: int =10) -> list[Message]:
    stms = select(Message).order_by(Message.created_at.desc()).limit(limit)
    message: Sequence[Message] = db.scalars(stms).all()
    return list(message[::-1])