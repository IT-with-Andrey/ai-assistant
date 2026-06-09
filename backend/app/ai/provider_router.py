import asyncio
from typing import AsyncGenerator, List
from backend.app.ai.providers.base import BaseLLMProvider
from backend.app.core.logger import logger

class ProviderError(Exception):
    """Ошибка провайдера при невозможности выполнить запрос."""
    pass
class ProviderRouter(BaseLLMProvider):
    """Роутер для управления ИИ-провайдерами (сейчас работает напрямую с Gemini)."""

    def __init__(self, providers: List[BaseLLMProvider]):
        self.providers = providers

    async def generate_response(self, messages: list, **kwargs) -> str:
        for provider in self.providers:
            if hasattr(provider, 'is_available') and not provider.is_available:
                logger.debug(f"Провайдер {provider.__class__.__name__} недоступен, пропускаем")
                continue

            try:
                logger.debug(f"ProviderRouter: пробуем {provider.__class__.__name__}")
                result = await provider.generate_response(messages, **kwargs)
                logger.debug(f"ProviderRouter: успешный ответ от {provider.__class__.__name__}")
                
                return  result
            except ProviderError as e:
                logger.warning(f"Провайдер {provider.__class__.__name__} отказал: {e}")
            except Exception as e:
                logger.error(f"Критический сбой в {provider.__class__.__name__}: {e}", exc_info=True)

        return "Извините, облачный ИИ-провайдер временно недоступен."

    async def generate_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        logger.debug("ProviderRouter: инициализация стрима")
        for provider in self.providers:
            if hasattr(provider, 'is_available') and not provider.is_available:
                continue

            try:
                logger.debug(f"ProviderRouter: пробуем стрим через {provider.__class__.__name__}")
                
                raw_stream = await provider.generate_stream(messages, **kwargs)

                # Безопасно получаем итератор стрима
                iterator = raw_stream.__aiter__()
                first_token = await iterator.__anext__()
                logger.debug(f"ProviderRouter: первый токен получен от {provider.__class__.__name__}")

                
                return self._stream_wrapper(first_token, iterator, provider.__class__.__name__)

            except ProviderError as e:
                logger.warning(f"Провайдер {provider.__class__.__name__} не смог начать стрим: {e}")
            except Exception as e:
                logger.error(f"Критическая ошибка стрима в {provider.__class__.__name__}: {e}", exc_info=True)
                continue

        return self._error_stream("Не удалось подключиться к модели генерации текста.")

    async def _stream_wrapper(self, first_token: str, iterator, provider_name: str) -> AsyncGenerator[str, None]:
        """Вспомогательный генератор: отдаёт первый сохраненный токен, а затем все остальные."""
        if first_token:
            logger.debug(f"Отдаю первый токен: {first_token[:50]}...")
            yield first_token
        try:
            async for token in iterator:
                logger.debug(f"Отдаю токен: {token[:50]}...")
                yield token
        except Exception as e:
            logger.error(f"Стрим провайдера {provider_name} прерван: {e}", exc_info=True)
            yield f"\n\n[⚠️ Ошибка: {e}]"

    async def _error_stream(self, error_msg: str) -> AsyncGenerator[str, None]:
        yield f"Ошибка системы: {error_msg}"
