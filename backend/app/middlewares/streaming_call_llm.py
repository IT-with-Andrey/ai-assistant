
from .base import BaseMiddleware , ChatContext 
from backend.app.core.logger import logger
from backend.app.ai.providers.base import BaseLLMProvider

class StreamingCallLLMMiddleware(BaseMiddleware):
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def process(self, ctx: ChatContext) -> ChatContext:
        logger.debug("StreamingCallLLMMiddleware: инициализация стрима LLM")
        try:
            ctx.response_stream = await self.llm_provider.generate_stream(ctx.llm_context)
            logger.debug("StreamingCallLLMMiddleware: стрим успешно создан")
        except Exception as e:
            logger.error(f"StreamingCallLLMMiddleware: ошибка создания стрима: {e}", exc_info=True)
            raise
        return ctx