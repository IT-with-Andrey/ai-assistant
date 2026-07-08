import asyncio
from .base import BaseMiddleware, ChatContext
from backend.app.core.logger import logger

# Мусор, который не сохраняем в память
JUNK_PATTERNS = (
    "INFO:", "DEBUG:", "WARNING:", "ERROR:", "Traceback", "File \"",
    "uvicorn", "ollama", "python -m", ".venv", "backend\\app",
    "asyncio", "sqlalchemy", "chromadb", "mem0",
)

class UpdateMemoryMiddleware(BaseMiddleware):
    def __init__(self, memory_orchestrator, background_tasks=None):
        self.memory_orchestrator = memory_orchestrator
        self.background_tasks = background_tasks

    def _is_junk(self, text: str) -> bool:
        """Проверяет, является ли текст мусором (логи, пути, пустые строки)."""
        if not text or not text.strip():
            return True
        text_upper = text.strip()
        # Слишком длинное — скорее всего логи
        if len(text_upper) > 2000:
            return True
        # Проверяем паттерны
        for pattern in JUNK_PATTERNS:
            if pattern in text_upper:
                return True
        # Проверяем, что это не команда
        if text_upper.startswith("/"):
            return True
        return False

    async def process(self, ctx: ChatContext) -> ChatContext:
        if self._is_junk(ctx.user_input):
            logger.debug(f"UpdateMemoryMiddleware: пропускаем мусор: {ctx.user_input[:50]}...")
            return ctx

        if self.background_tasks:
            self.background_tasks.add_task(self._update_memory, ctx.user_id, ctx.user_input, ctx.persona_id)
            logger.debug("UpdateMemoryMiddleware: задача поставлена в фоновые задачи")
        else:
            await self._update_memory(ctx.user_id, ctx.user_input, ctx.persona_id)
        return ctx

    async def _update_memory(self, user_id, text, persona_id=None):
        try:
            await self.memory_orchestrator.add_user_memory(user_id, text=text, persona_id=persona_id)
            logger.debug(f"UpdateMemoryMiddleware: факт сохранён: {text[:100]}...")
        except Exception as e:
            logger.error(f"Ошибка сохранения в память: {e}", exc_info=True)