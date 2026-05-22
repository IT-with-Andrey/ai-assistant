
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy.orm import Session

from backend.app.database.models import UserFact
from backend.app.ai.context_builder import build_context

# Используем общую фикстуру db_session из tests/conftest.py
# (убедитесь, что conftest.py содержит соответствующую фикстуру)


def test_build_context_includes_all_facts(db_session: Session):
    # 10 фактов напрямую в user_facts
    facts = [
        ("name", "Меня зовут Алиса."),
        ("goal", "Моя цель — выучить Python."),
        ("interest", "Я интересуюсь машинным обучением."),
        ("preference", "Я предпочитаю тёмную тему в редакторе."),
        ("fact", "Я работаю инженером в IT-компании."),
        ("name", "Моё второе имя — Боб."),
        ("goal", "Хочу пробежать марафон."),
        ("interest", "Увлекаюсь астрономией."),
        ("preference", "Люблю кофе по утрам."),
        ("fact", "Живу в городе Нск."),
    ]
    for key, value in facts:
        db_session.add(UserFact(key=key, value=value))
    db_session.commit()

    # Получаем факты и собираем контекст
    user_facts = db_session.query(UserFact).all()
    context_messages = build_context(
        history=[],
        user_input="Что ты знаешь обо мне?",
        summary=None,
        user_facts=user_facts
    )

    # Склеиваем контент всех сообщений
    full_context = " ".join(
        msg.get("content", "") for msg in context_messages
    )

    # Проверяем, что все значения фактов присутствуют
    missing = [value for _, value in facts if value not in full_context]
    assert len(missing) == 0, (
        f"Не все факты попали в контекст. Отсутствуют: {missing}"
    )