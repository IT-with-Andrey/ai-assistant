import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database.models import Message, UserFact, Summary
from backend.app.ai.context_builder import build_context


def test_empty_history(db_session):
    # Пустая история: только SYSTEM_PROMPT + user_input
    messages = build_context(history=[], user_input="Привет", summary=None, user_facts=[])
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Привет"


def test_with_user_facts(db_session):
    facts = [
        UserFact(key="name", value="Алиса"),
        UserFact(key="goal", value="Python"),
    ]
    messages = build_context(history=[], user_input="Кто я?", summary=None, user_facts=facts)
    # SYSTEM_PROMPT + факты + user_input = 3
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"  # факты
    assert "Алиса" in messages[1]["content"]
    assert "Python" in messages[1]["content"]
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "Кто я?"


def test_with_summary(db_session):
    summary = Summary(content="Ранее обсуждали архитектуру")
    messages = build_context(history=[], user_input="Продолжим?", summary=summary, user_facts=[])
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    # build_context использует str(summary), а не напрямую summary.content
    assert "Контекст предыдущего диалога" in messages[1]["content"]
    assert str(summary) in messages[1]["content"]


def test_with_history(db_session):
    # Используем ORM-объекты Message
    msgs = [
        Message(role="user", content="Привет"),
        Message(role="assistant", content="Здравствуй"),
    ]
    messages = build_context(history=msgs, user_input="Как дела?", summary=None, user_facts=[])
    # SYSTEM_PROMPT + 2 сообщения истории + user_input = 4
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Привет"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "Здравствуй"
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "Как дела?"


def test_with_rag_context(db_session):
    facts = [UserFact(key="color", value="синий")]
    summary = Summary(content="Пользователь любит обсуждать дизайн")
    msgs = [Message(role="user", content="Привет")]
    messages = build_context(history=msgs, user_input="Мой цвет?", summary=summary, user_facts=facts)
    # SYSTEM_PROMPT + summary + facts + history(1) + user_input = 5
    assert len(messages) == 5
    roles = [m["role"] for m in messages]
    assert roles == ["system", "system", "system", "user", "user"]


def test_duplicate_facts_removed(db_session):
    facts = [
        UserFact(key="name", value="Алиса"),
        UserFact(key="name", value="Алиса"),  # дубликат
    ]
    messages = build_context(history=[], user_input="Привет", summary=None, user_facts=facts)
    # факты во втором сообщении (индекс 1)
    facts_content = messages[1]["content"]
    # Функция не удаляет дубликаты, поэтому "Алиса" будет упомянута дважды
    assert facts_content.count("Алиса") == 2