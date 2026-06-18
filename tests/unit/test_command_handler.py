import pytest
from unittest.mock import AsyncMock
from backend.app.middlewares.base import ChatContext
from backend.app.middlewares.command_handler import CommandHandlerMiddleware

@pytest.fixture
def memory_orch():
    return AsyncMock()

@pytest.fixture
def middleware(memory_orch):
    return CommandHandlerMiddleware(memory_orch)

@pytest.mark.asyncio
async def test_no_command_passes_through(middleware):
    ctx = ChatContext(user_input="Привет!")
    result = await middleware.process(ctx)
    assert result.response is None
    assert not result.should_stop

@pytest.mark.asyncio
async def test_help_command(middleware):
    ctx = ChatContext(user_input="/help")
    result = await middleware.process(ctx)
    assert "Доступные команды" in result.response
    assert result.should_stop

@pytest.mark.asyncio
async def test_role_command_valid(middleware, memory_orch):
    ctx = ChatContext(user_input="/role python_teacher")
    result = await middleware.process(ctx)
    assert "успешно сменена" in result.response
    memory_orch.add_user_memory.assert_called_once()

@pytest.mark.asyncio
async def test_role_command_invalid(middleware):
    ctx = ChatContext(user_input="/role invalid_role")
    result = await middleware.process(ctx)
    assert "Неверная роль" in result.response