import pytest
from unittest.mock import AsyncMock
from backend.app.ai.memory.episodic import EpisodicMemory

@pytest.fixture
def mock_memory_orch():
    return AsyncMock()

@pytest.fixture
def episodic(mock_memory_orch):
    return EpisodicMemory(mock_memory_orch)

@pytest.mark.asyncio
async def test_log_event_saves_to_global(episodic, mock_memory_orch):
    data = {"user_message": "Привет", "assistant_response": "Здравствуй", "importance": 5}
    await episodic.log_event("user1", "default", "message", data)
    mock_memory_orch.add_user_memory.assert_called_once()
    args = mock_memory_orch.add_user_memory.call_args[1]
    assert args['persona_id'] is None
    assert 'message' in args['text']
    assert args['metadata']['event_type'] == 'message'

@pytest.mark.asyncio
async def test_get_recent_events_filters(episodic, mock_memory_orch):
    # Возвращаем список словарей с метаданными
    mock_memory_orch.get_user_fact.return_value = [
        {'text': 'event1', 'metadata': {'event_type': 'message', 'user_id': 'user1', 'persona_id': 'default', 'timestamp': 100}},
        {'text': 'event2', 'metadata': {'event_type': 'message', 'user_id': 'user2', 'persona_id': 'default', 'timestamp': 200}},
        {'text': 'event3', 'metadata': {'event_type': 'message', 'user_id': 'user1', 'persona_id': 'other', 'timestamp': 150}},
    ]
    events = await episodic.get_recent_events("user1", "default", limit=10)
    assert len(events) == 1
    assert events[0]['text'] == 'event1'