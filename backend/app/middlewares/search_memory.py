from .base import BaseMiddleware, ChatContext
from backend.app.core.logger import logger

class SearchMemoryMiddleware(BaseMiddleware):
    def __init__(self, memory_orchestrator):
        self.memory_orchestrator = memory_orchestrator

    async def process(self, ctx: ChatContext) -> ChatContext:
        logger.debug("SearchMemoryMiddleware: поиск фактов в памяти")
        try:
            ctx.facts = await self.memory_orchestrator.search_relevant_facts(
                ctx.user_id, 
                query=ctx.user_input,
                limit = 3,
                persona_id=ctx.persona_id
            )
            if ctx.facts:
                logger.debug(f"Найдены факты: {ctx.facts[:100]}...")
            else:
                logger.debug("Релевантные факты не найдены")
            
        except Exception as e:
            logger.error(f"Ошибка извлечения фактов из памяти: {e}", exc_info=True)
            ctx.facts = ""   # не роняем стрим
        return ctx