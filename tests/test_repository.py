import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy.orm import Session

from backend.app.database.repository import (
    save_message,
    get_last_messages,
    save_user_fact,
    get_all_user_facts,
    save_summary,
)
from backend.app.database.models import Message, UserFact, Summary


def test_save_message(db_session: Session):
    msg = save_message(db_session, role="user", content="Привет!")
    assert msg.id is not None
    assert msg.role == "user"
    assert msg.content == "Привет!"
    assert msg.timestamp is not None

    # Проверяем в базе
    saved = db_session.query(Message).filter_by(id=msg.id).first()
    assert saved is not None
    assert saved.content == "Привет!"


def test_get_last_messages(db_session: Session):
    # Пустая история — пустой список
    assert get_last_messages(db_session, limit=5) == []

    # Заполняем 10 сообщений
    for i in range(1, 11):
        save_message(db_session, role="user", content=f"msg{i}")

    # Получаем последние 5
    last_5 = get_last_messages(db_session, limit=5)
    assert len(last_5) == 5
    # Должны быть сообщения 6..10, порядок — по возрастанию id (как в истории)
    contents = [m.content for m in last_5]
    assert contents == [f"msg{i}" for i in range(6, 11)]

    # Лимит больше общего числа — вернутся все 10
    last_all = get_last_messages(db_session, limit=20)
    assert len(last_all) == 10


def test_save_user_fact(db_session: Session):
    fact = save_user_fact(db_session, key="name", value="Алиса")
    assert fact.id is not None
    assert fact.key == "name"
    assert fact.value == "Алиса"

    saved = db_session.query(UserFact).filter_by(id=fact.id).first()
    assert saved is not None
    assert saved.value == "Алиса"


def test_get_all_user_facts(db_session: Session):
    # Изначально пусто
    assert get_all_user_facts(db_session) == []

    save_user_fact(db_session, key="name", value="Алиса")
    save_user_fact(db_session, key="goal", value="Python")

    facts = get_all_user_facts(db_session)
    assert len(facts) == 2
    keys = {f.key for f in facts}
    assert keys == {"name", "goal"}


def test_save_summary(db_session: Session):
    summary = save_summary(db_session, content="Обсуждение архитектуры")
    assert summary.id is not None
    assert summary.content == "Обсуждение архитектуры"
    # Может быть поле created_at, если есть
    if hasattr(summary, 'created_at'):
        assert summary.created_at is not None

    saved = db_session.query(Summary).filter_by(id=summary.id).first()
    assert saved is not None
    assert saved.content == "Обсуждение архитектуры"