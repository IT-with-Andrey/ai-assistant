

from backend.app.middlewares.base import BaseMiddleware, ChatContext
from backend.app.core.logger import logger

class MemoryManagerMiddleware(BaseMiddleware):
    def __init__(self, memory_manager, background_tasks=None):
        self.manager = memory_manager
        self.background_tasks = background_tasks

    async def process(self, ctx: ChatContext) -> ChatContext:
        # Запускаем обработку памяти для любого пользовательского ввода,
        # даже если ответ от ассистента ещё не готов (стрим).
        if ctx.user_input:
            logger.debug(
                f"MemoryManagerMiddleware: запуск фоновой обработки памяти "
                f"(user={ctx.user_id}, persona={ctx.persona_id})"
            )
            if self.background_tasks:
                self.background_tasks.add_task(
                    self.manager.process_memory_pipeline,
                    ctx.user_id,
                    ctx.persona_id,
                    ctx.user_input,
                    ctx.response or ""   # при стриме ответ будет пустым
                )
            else:
                await self.manager.process_memory_pipeline(
                    ctx.user_id,
                    ctx.persona_id,
                    ctx.user_input,
                    ctx.response or ""
                )
        return ctx