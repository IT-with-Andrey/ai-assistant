
import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from backend.app.services.assistant_service import chat
from backend.app.database.models import Message, UserFact
from backend.app.ai.prompts import SYSTEM_PROMPT


def test_conversation_memory_flow(db_session: Session):
    """
    Имитация полного цикла общения с консолидацией памяти.
    Проверяем, что после 12 сообщений:
      - В user_facts появились записи.
      - В messages осталось ровно 6 последних сообщений.
    """
    fake_llm_response = '[{"key": "favorite_topic", "value": "memory tests"}]'

    with patch("backend.app.services.assistant_service.generate_response",
               return_value=fake_llm_response) as mock_llm:
        for i in range(1, 13):
            user_input = f"Пользовательское сообщение номер {i}"
            chat(user_input, db_session)

        # Проверка 1: Сообщений осталось 6 (SUMMARY_TRIGGER)
        remaining_messages = db_session.query(Message).count()
        assert remaining_messages == 6, (
            f"Ожидалось 6 сообщений, осталось {remaining_messages}"
        )

        # Проверка 2: Факты сохранены
        facts = db_session.query(UserFact).all()
        assert len(facts) > 0, "Таблица user_facts пуста – консолидация не отработала"

        # Проверка 3: Факт содержит ожидаемые данные
        target_fact = db_session.query(UserFact).filter(
            UserFact.key == "favorite_topic"
        ).first()
        assert target_fact is not None, "Факт с ключом 'favorite_topic' не найден"
        assert target_fact.value == "memory tests"

        # Проверка 4: LLM вызывалась
        assert mock_llm.called, "generate_response не вызывалась"


def test_extraction_with_new_keys_and_system_prompt(db_session: Session):
    """
    Проверяет новую логику извлечения фактов с обновлёнными ключами
    (name, goal, interest, preference, fact) и внедрение SYSTEM_PROMPT
    в промпт, передаваемый модели.
    """
    # Записываем все аргументы, с которыми вызывается generate_response
    call_args_list = []

    def mock_generate_response(*args, **kwargs):
        call_args_list.append((args, kwargs))
        # Возвращаем JSON-массив с новыми ключами фактов
        return (
            '[{"key": "name", "value": "Анна"}, '
            '{"key": "goal", "value": "изучить Python"}, '
            '{"key": "interest", "value": "машинное обучение"}, '
            '{"key": "preference", "value": "тёмная тема"}, '
            '{"key": "fact", "value": "работает инженером"}]'
        )

    with patch("backend.app.services.assistant_service.generate_response",
               side_effect=mock_generate_response):
        for i in range(1, 13):
            chat(f"Сообщение {i}", db_session)

    # 1. Проверяем наличие всех ожидаемых ключей в user_facts
    expected_keys = {"name", "goal", "interest", "preference", "fact"}
    facts = db_session.query(UserFact).all()
    saved_keys = {fact.key for fact in facts}
    assert expected_keys.issubset(saved_keys), (
        f"Не все ожидаемые ключи сохранены: {saved_keys}"
    )

    # 2. Проверяем, что SYSTEM_PROMPT передавался модели
    # Ищем "персонализированный помощник" — это уникальная часть нового SYSTEM_PROMPT
    found = False
    for args, kwargs in call_args_list:
        args_repr = str(args) + str(kwargs)
        if "персонализированный помощник" in args_repr:
            found = True
            break
    assert found, "SYSTEM_PROMPT не обнаружен ни в одном вызове generate_response"