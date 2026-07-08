"""
Асинхронный адаптер ProviderRouter -> LangChain LLM.
"""
from typing import Any, List, Optional
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from backend.app.core.logger import logger

class RouterLLM(LLM):
    """Обёртка над ProviderRouter с нативной асинхронной поддержкой."""
    provider_router: Any

    def __init__(self, provider_router):
        super().__init__(provider_router=provider_router)

    @property
    def _llm_type(self) -> str:
        return "router_llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        raise NotImplementedError("RouterLLM работает только асинхронно. Используйте ainvoke().")

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.provider_router.generate_response(messages)
            return response
        except Exception as e:
            logger.error(f"RouterLLM async error: {e}")
            raise