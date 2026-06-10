from typing import List, Dict, AsyncGenerator, Tuple, Optional 
from google import genai
from google.genai import types
from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.ai.providers.base import BaseLLMProvider
from backend.app.ai.provider_router import ProviderError

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash", on_model_switch=None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self.client = None
        self.is_available = True
        
        
        # Вместо жесткого падения — мягко маркируем провайдера как неактивного
        if not self.api_key:
            logger.error("⚠️ GEMINI_API_KEY не найден в конфигурации! GeminiProvider отключен.")
            self.is_available = False
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.debug("GeminiProvider: клиент успешно инициализирован")
        except Exception as e:
            logger.error(f"⚠️ Ошибка инициализации клиента Gemini: {e}")
            self.is_available = False

        self.fallback_models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]
        if self.model_name in self.fallback_models:
            self.fallback_models.remove(self.model_name)
        logger.debug(f"GeminiProvider: основная модель {self.model_name}, резервные: {self.fallback_models}")

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.is_available:
            raise ProviderError("GeminiProvider недоступен (отсутствует API-ключ или сбой клиента)")
        
        logger.debug("GeminiProvider: начало генерации ответа")
        models_to_try = [self.model_name] + self.fallback_models
        contents, system_instruction = self._parse_messages(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=kwargs.get("temperature", 0.7)
        )

        last_error = None
        for model in models_to_try:
            try:
                logger.debug(f"GeminiProvider: попытка модели {model}")
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                if not response.text:
                    raise ProviderError("Получен пустой ответ от Gemini")
                
                logger.debug(f"GeminiProvider: успешный ответ от модели {model}")
                return response.text
            except Exception as e:
                logger.warning(f"Gemini модель {model} ошибка: {e}", exc_info=True)
                last_error = e
                
        raise ProviderError(f"Gemini все модели отказали. Последняя ошибка: {last_error}")

    async def generate_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        if not self.is_available:
            raise ProviderError("GeminiProvider недоступен (отсутствует API-ключ или сбой клиента)")
        logger.debug("GeminiProvider: начало стрим-генерации")

        models_to_try = [self.model_name] + self.fallback_models
        contents, system_instruction = self._parse_messages(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=kwargs.get("temperature", 0.7)
        )

        last_error = None
        for model in models_to_try:
            try:
                logger.debug(f"GeminiProvider: попытка стрима через модель {model}")
                stream = await self.client.aio.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=config
                )
                
                logger.debug(f"GeminiProvider: стрим для модели {model} успешно создан")

                async def _safe_stream_wrapper():
                    try:
                        async for chunk in stream:
                            if chunk.text:
                                yield chunk.text
                    except Exception as e:
                        logger.error(f"Ошибка во время чтения стрима Gemini: {e}", exc_info=True)
                        yield f"\n[Ошибка стрима: {e}]"
                    finally:
                        if hasattr(stream, 'aclose'):
                            await stream.aclose()
                            
                return _safe_stream_wrapper()
            except Exception as e:
                logger.warning(f"Gemini модель {model} ошибка стрима: {e}", exc_info=True)
                last_error = e
                
        raise ProviderError(f"Gemini все модели отказали для стрима. Последняя ошибка: {last_error}")

    def _parse_messages(self, messages: List[Dict[str, str]]) -> Tuple[List[Dict], Optional[str]]:
        contents = []
        system_instruction = None
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
        return contents, system_instruction