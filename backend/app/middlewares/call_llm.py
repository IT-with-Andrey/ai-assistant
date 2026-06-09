from .base import BaseMiddleware, ChatContext
from backend.app.ai.providers.base import BaseLLMProvider
from backend.app.core.logger import logger

class CallLLMMiddleware(BaseMiddleware):
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def process(self, ctx: ChatContext) -> ChatContext:
        logger.debug("CallLLMMiddleware: отправка запроса к LLM")
        try:
            ctx.response = await self.llm_provider.generate_response(ctx.llm_context)
            logger.debug("CallLLMMiddleware: ответ от LLM получен")
        except Exception as e:
            logger.error(f"CallLLMMiddleware: ошибка при вызове LLM: {e}", exc_info=True)
            raise
        return ctx