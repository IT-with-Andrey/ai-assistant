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
        logger.debug("ProviderRouter: инициализация стрима с перебором провайдеров")
        return self._smart_stream_generator(messages, list(self.providers), **kwargs)
    

    async def _smart_stream_generator(self, messages: list, providers: List[BaseLLMProvider], **kwargs):
        """Генератор, который при ошибке переходит к следующему провайдеру."""
        current_provider_index = 0
        while current_provider_index < len(providers):
            provider = providers[current_provider_index]
            if hasattr(provider, 'is_available') and not provider.is_available:
                logger.debug(f"Провайдер {provider.__class__.__name__} недоступен, пропускаем")
                current_provider_index += 1
                continue

            try:
                logger.debug(f"ProviderRouter: пробуем стрим через {provider.__class__.__name__}")
                raw_stream = await provider.generate_stream(messages, **kwargs)
                iterator = raw_stream.__aiter__()

                # Читаем токены, пока не кончатся или не возникнет ошибка
                while True:
                    try:
                        token = await iterator.__anext__()
                        yield token
                    except StopAsyncIteration:
                        return  # Стрим завершился успешно
                    except Exception as e:
                        logger.warning(f"Стрим {provider.__class__.__name__} прервался: {e}")
                        break  # Выходим из цикла чтения, чтобы переключить провайдера
            except Exception as e:
                logger.error(f"ProviderRouter: ошибка в стриме {provider.__class__.__name__}: {e}", exc_info=True)
                logger.warning(f"Провайдер {provider.__class__.__name__} не смог начать стрим: {e}")

            # Переходим к следующему провайдеру
            current_provider_index += 1

        # Все провайдеры отказали
        logger.debug(f"ProviderRouter: начал стримить через {provider.__class__.__name__}")
        yield "Извините, все языковые модели временно недоступны. Попробуйте позже."