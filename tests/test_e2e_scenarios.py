import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import patch
from backend.app.database.models import UserFact
from backend.app.services.assistant_service import chat


def test_acquaintance_scenario(db_session):
    facts = [
        ("name", "Меня зовут Борис."),
        ("goal", "Хочу выучить Rust."),
        ("interest", "Люблю видеоигры."),
        ("preference", "Тёмная тема."),
        ("fact", "Живу в Москве."),
    ]
    extraction_response = "[" + ", ".join(
        [f'{{"key": "{k}", "value": "{v}"}}' for k, v in facts]
    ) + "]"

    def mock_generate_response(prompt, *args, **kwargs):
        if "Извлеки" in str(prompt):
            return extraction_response
        return "Я знаю: " + "; ".join([v for _, v in facts]) + "."

    with patch("backend.app.services.assistant_service.MAX_HISTORY", 2), \
         patch("backend.app.services.assistant_service.SUMMARY_TRIGGER", 2), \
         patch("backend.app.services.assistant_service.generate_response", side_effect=mock_generate_response):
        for _, msg in facts:
            chat(msg, db_session)
        chat("Сохрани всё.", db_session)
        answer = chat("Что ты знаешь обо мне?", db_session)

    found = sum(1 for _, v in facts if v in answer)
    assert found == len(facts), f"Найдено {found}/{len(facts)} фактов"
    assert db_session.query(UserFact).count() >= len(facts)


def test_forgetfulness_scenario(db_session):
    facts = [
        ("name", "Я Алексей."),
        ("fact", "Работаю в банке."),
    ]
    extraction_response = "[" + ", ".join(
        [f'{{"key": "{k}", "value": "{v}"}}' for k, v in facts]
    ) + "]"

    def mock_generate_response(prompt, *args, **kwargs):
        if "Извлеки" in str(prompt):
            return extraction_response
        found = [v for _, v in facts if v in str(prompt)]
        return "Вот что помню: " + "; ".join(found) + "."

    with patch("backend.app.services.assistant_service.MAX_HISTORY", 2), \
         patch("backend.app.services.assistant_service.SUMMARY_TRIGGER", 2), \
         patch("backend.app.services.assistant_service.generate_response", side_effect=mock_generate_response):
        for _, msg in facts:
            chat(msg, db_session)
        chat("Сохрани.", db_session)
        answer = chat("Что ты знаешь обо мне?", db_session)

    assert "Алексей" in answer or "банке" in answer
    assert db_session.query(UserFact).count() >= len(facts)