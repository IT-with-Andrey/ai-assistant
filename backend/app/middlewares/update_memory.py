import asyncio
from .base import BaseMiddleware, ChatContext
from backend.app.core.logger import logger

class UpdateMemoryMiddleware(BaseMiddleware):
    def __init__(self, memory_orchestrator, background_tasks=None):
        self.memory_orchestrator = memory_orchestrator
        self.background_tasks = background_tasks

    async def process(self, ctx: ChatContext) -> ChatContext:
        if self.background_tasks:
            # Создаём асинхронную задачу и добавляем её к ожиданию завершения
            task = asyncio.create_task(self._update_memory(ctx.user_id, ctx.user_input))
            self.background_tasks.add_task(task)
            logger.debug("UpdateMemoryMiddleware: задача поставлена в фоновые задачи")
        else:
            await self._update_memory(ctx.user_id, ctx.user_input)
            
        return ctx

    async def _update_memory(self, user_id, text, persona_id = None):
        try:
            await self.memory_orchestrator.add_user_memory(user_id, text=text , persona_id=persona_id)
            logger.debug(f"UpdateMemoryMiddleware: факт сохранён (persona={persona_id}): {text[:100]}...")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в память: {e}", exc_info=True)