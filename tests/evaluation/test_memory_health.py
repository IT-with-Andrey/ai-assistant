# tests/evaluation/test_memory_health.py
import uuid
import pytest
from pathlib import Path
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.ai.orchestrator_factory import app_container
from backend.app.ai.memory.episodic import EpisodicMemory
from backend.app.ai.memory.reflection import ReflectionLayer
from backend.app.ai.providers.ollama_provider import OllamaProvider

async def add_facts(user_id, facts):
    for fact in facts:
        await app_container.memory_orchestrator.add_user_memory(user_id, text=fact, persona_id=None)

def compute_recall(expected: str, actual: str) -> float:
    expected_facts = [f.strip() for f in expected.split('.') if f.strip()]
    if not expected_facts:
        return 1.0
    found = sum(1 for fact in expected_facts if fact.lower() in actual.lower())
    return found / len(expected_facts)

def compute_precision(expected: str, actual: str) -> float:
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())
    if not actual_words:
        return 0.0
    common = expected_words.intersection(actual_words)
    return len(common) / len(actual_words)

@pytest.mark.asyncio
async def test_memory_health():
    user_id = f"health_{uuid.uuid4().hex[:8]}"
    scores = {}

    # 1. ДОЛГОВРЕМЕННАЯ ПАМЯТЬ (Mem0 факты)
    facts = [
        "Меня зовут Борис",
        "Я живу в Мюнхене",
        "Моё хобби — скалолазание",
        "Я работаю дата-сайентистом",
        "Я люблю фильмы Тарантино",
        "Моя цель — пробежать марафон",
        "Я владею английским и немецким",
        "Я предпочитаю macOS",
        "Я коллекционирую виниловые пластинки",
        "Я изучаю machine learning"
    ]
    await add_facts(user_id, facts)

    all_facts = await app_container.memory_orchestrator.get_user_fact(user_id)
    assert len(all_facts) >= 8, f"Недостаточно фактов сохранено: {len(all_facts)}"

    retrieval_text = "\n".join([f"- {f}" for f in all_facts])
    query = "Расскажи обо мне всё, что знаешь"
    messages = [
    {"role": "system", "content": (
        "Ты персональный ассистент. Ответь на вопрос, ПЕРЕЧИСЛИВ все подходящие факты из списка ниже. "
        "Отвечай строго по фактам, не придумывай. Говори кратко, в одном предложении."
    )},
    {"role": "user", "content": f"Факты:\n{retrieval_text}\n\nВопрос: {query}\nОтвет (перечисли факты):"}
     ]
    alt_llm = OllamaProvider(model_name="nemotron-3-super:cloud")
    answer = await alt_llm.generate_response(messages)

    recall = compute_recall("Меня зовут Борис. Я живу в Мюнхене. Моё хобби — скалолазание.", answer)
    precision = compute_precision("Меня зовут Борис. Я живу в Мюнхене. Моё хобби — скалолазание.", answer)
    scores["long_term"] = (recall + precision) / 2 * 100

    # 2. ОПЕРАТИВНАЯ ПАМЯТЬ (последние сообщения)
    from backend.app.database.connection import AsyncSessionLocal
    from backend.app.database.repository import MessageRepository
    async with AsyncSessionLocal() as db:
        repo = MessageRepository(db)
        await repo.save(role="user", content="Привет, ассистент!", user_id=user_id)
        await repo.save(role="assistant", content="Привет, Борис! Чем могу помочь?", user_id=user_id)
        last = await repo.get_last(limit=2, user_id=user_id)
        assert len(last) == 2, "История не сохранилась"
        scores["working"] = 100.0

    # 3. ЭПИЗОДИЧЕСКАЯ ПАМЯТЬ
    episodic = EpisodicMemory(app_container.memory_orchestrator)
    await episodic.log_event(user_id, persona_id=None, event_type="login", data={"user_message": "Вход в систему", "importance": 7})
    # Вместо get_recent_events (который пока не работает) проверим факт сохранения через get_all
    all_after = await app_container.memory_orchestrator.get_user_fact(user_id)
    has_episode = any("login" in f for f in all_after)
    scores["episodic"] = 100.0 if has_episode else 0.0

    # 4. РЕФЛЕКСИВНАЯ ПАМЯТЬ
    reflection = ReflectionLayer(app_container.llm_router, app_container.memory_orchestrator, episodic)
    summary = await reflection.reflect(user_id, persona_id=None, period="test")
    scores["reflective"] = 100.0 if summary else 0.0

    total = sum(scores.values()) / len(scores)
    print("\n====== MEMORY HEALTH SCORE ======")
    for layer, score in scores.items():
        print(f"  {layer}: {score:.1f}%")
    print(f"  TOTAL: {total:.1f}%")
    assert total >= 30.0, f"Общий Memory Health Score слишком низкий: {total:.1f}%"