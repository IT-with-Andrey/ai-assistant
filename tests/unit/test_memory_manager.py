import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.ai.memory.manager import MemoryManager, ExtractedFact, MemoryPayload

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate_response.return_value = "<score>8</score>"
    return llm

@pytest.fixture
def mock_memory_orch():
    return AsyncMock()

@pytest.fixture
def mock_episodic():
    return AsyncMock()

@pytest.fixture
def manager(mock_llm, mock_memory_orch, mock_episodic):
    return MemoryManager(mock_llm, mock_memory_orch, mock_episodic)

@pytest.mark.asyncio
async def test_assess_importance_parses_score(manager, mock_llm):
    score = await manager.assess_importance("Я люблю Python", "Это здорово!", user_id="test", persona_id=None)
    assert score == 8

@pytest.mark.asyncio
async def test_assess_importance_default_on_garbage(manager, mock_llm):
    mock_llm.generate_response.return_value = "какая-то ерунда без чисел"
    score = await manager.assess_importance("Привет", "Привет!", user_id="test", persona_id=None)
    assert score == manager.DEFAULT_IMPORTANCE

@pytest.mark.asyncio
async def test_extract_atomic_facts_success(manager, mock_llm):
    mock_llm.generate_response.return_value = '''{"facts": [{"fact": "Создатель любит Python", "category": "preferences"}]}'''
    facts = await manager.extract_atomic_facts("Люблю Python", "Отлично!", user_id="test", persona_id=None)
    assert len(facts) == 1
    assert facts[0].fact == "Создатель любит Python"

@pytest.mark.asyncio
async def test_extract_atomic_facts_cleans_markdown(manager, mock_llm):
    mock_llm.generate_response.return_value = '''```json
{"facts": [{"fact": "Создатель живет в Берлине", "category": "biography"}]}
```'''
    facts = await manager.extract_atomic_facts("Я в Берлине", "Понял", user_id="test", persona_id=None)
    assert len(facts) == 1
    assert facts[0].fact == "Создатель живет в Берлине"

@pytest.mark.asyncio
async def test_process_memory_pipeline_above_threshold(manager, mock_llm, mock_memory_orch, mock_episodic):
    mock_llm.generate_response.side_effect = [
        "<score>7</score>",  # оценка важности
        '{"facts": [{"fact": "Создатель знает Python", "category": "work"}]}'  # факты
    ]
    await manager.process_memory_pipeline("test_user", "default", "Я знаю Python", "Отлично")
    assert mock_episodic.log_event.called
    assert mock_memory_orch.add_user_memory.called

@pytest.mark.asyncio
async def test_process_memory_pipeline_below_threshold(manager, mock_llm, mock_memory_orch, mock_episodic):
    mock_llm.generate_response.return_value = "<score>2</score>"
    await manager.process_memory_pipeline("test_user", "default", "Привет", "Привет")
    assert mock_episodic.log_event.called
    assert not mock_memory_orch.add_user_memory.called  # факты не должны сохраняться

@pytest.mark.asyncio
async def test_cache_importance(manager, mock_llm):
    mock_llm.generate_response.return_value = "<score>9</score>"
    score1 = await manager.assess_importance("Кэш тест", "Ответ", user_id="test", persona_id=None)
    assert score1 == 9
    # Второй вызов с теми же данными должен использовать кэш и не вызывать LLM
    mock_llm.generate_response.reset_mock()
    score2 = await manager.assess_importance("Кэш тест", "Ответ", user_id="test", persona_id=None)
    assert score2 == 9
    mock_llm.generate_response.assert_not_called()

@pytest.mark.asyncio
async def test_invalidate_cache(manager, mock_llm):
    mock_llm.generate_response.return_value = "<score>5</score>"
    await manager.assess_importance("Очистка", "Ок", user_id="test", persona_id=None)
    await manager.invalidate_cache()
    # После очистки кэша LLM должен вызваться снова
    mock_llm.generate_response.reset_mock()
    mock_llm.generate_response.return_value = "<score>5</score>"
    await manager.assess_importance("Очистка", "Ок", user_id="test", persona_id=None)
    assert mock_llm.generate_response.called