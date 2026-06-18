import pytest
from unittest.mock import AsyncMock
from backend.app.ai.memory_orchestrator import MemoryOrchestrator

@pytest.fixture
def mock_vector():
    return AsyncMock()

@pytest.fixture
def mock_pruner():
    return AsyncMock()

@pytest.fixture
def mock_optimizer():
    return AsyncMock()

@pytest.fixture
def orchestrator(mock_vector, mock_pruner, mock_optimizer):
    return MemoryOrchestrator(mock_vector, mock_pruner, mock_optimizer)

@pytest.mark.asyncio
async def test_add_user_memory(orchestrator, mock_vector):
    await orchestrator.add_user_memory("user1", "fact", persona_id="p1")
    mock_vector.add_memory.assert_called_with("user1", "fact", metadata=None, persona_id="p1")

@pytest.mark.asyncio
async def test_search_relevant_facts_formats(orchestrator, mock_vector):
    mock_vector.search_memories.return_value = ["fact1", "fact2"]
    result = await orchestrator.search_relevant_facts("user1", "query", persona_id="p1")
    assert "-fact1\n-fact2" in result