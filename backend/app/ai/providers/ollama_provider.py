import json
from typing import List, Dict, AsyncGenerator
import httpx
from .base import BaseLLMProvider
from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.core.logging_utils import log_execution_time
from backend.app.ai.provider_router import ProviderError

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name: str = None, host: str = None):
        self.model_name = model_name or settings.AI_MODEL
        self.host = host or settings.OLLAMA_HOST
        self.fallback_models = ["nemotron-3-super:cloud", "minimax-m3:cloud", "gemma4:31b-cloud"]

    @log_execution_time
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        logger.debug("Отправка запроса к Ollama: %d сообщений", len(messages))
        safe_messages = []
        for msg in messages:
            safe_msg = {
                'role': str(msg.get('role', 'user')),
                'content': str(msg.get('content', ''))
            }
            safe_messages.append(safe_msg)

        models_to_try = [self.model_name] if self.model_name else self.fallback_models
        last_error = None

        async with httpx.AsyncClient(timeout=120) as client:
            for model in models_to_try:
                try:
                    response = await client.post(
                        f"{self.host}/api/chat",
                        json={
                            "model": model,
                            "messages": safe_messages,
                            "stream": False,
                            'options': {'num_predict': 4096}
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    answer = data['message']['content']
                    logger.info('Ответ получен (длина %d символов)', len(answer))
                    return answer
                except httpx.HTTPStatusError as e:
                    logger.warning("Модель %s вернула ошибку HTTP %s: %s", model, e.response.status_code, e)
                    last_error = e
                except httpx.RequestError as e:
                    logger.warning("Сетевая ошибка при запросе модели %s: %s", model, e)
                    last_error = e
                except (KeyError, ValueError) as e:
                    logger.error("Ошибка парсинга ответа от Ollama: %s", e)
                    last_error = e

        if isinstance(last_error, httpx.HTTPStatusError):
            logger.error("Все модели вернули ошибки HTTP. Последняя: %s", last_error)
        elif isinstance(last_error, httpx.RequestError):
            logger.error("Все модели недоступны по сети. Последняя ошибка: %s", last_error)
        else:
            logger.error("Все модели вернули некорректные ответы.")
        
        raise ProviderError(f"Ollama: все модели недоступны. Последняя ошибка: {last_error}")

    async def generate_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        logger.debug("Стриминг-запрос к Ollama: %d сообщений", len(messages))

        # Внутренний генератор, имеет доступ к self и messages через замыкание
        async def _stream_tokens():
            try:
                safe_messages = []
                for msg in messages:
                    safe_msg = {
                        'role': str(msg.get('role', 'user')),
                        'content': str(msg.get('content', ''))
                    }
                    safe_messages.append(safe_msg)   # теперь все сообщения попадают в список
                model = self.model_name
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream(
                        'POST',
                        f"{self.host}/api/chat",
                        json={
                            "model": model,
                            "messages": safe_messages,
                            "stream": True,
                            "options": {'num_predict': 4096}
                        }
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                                token = data.get('message', {}).get('content', '')
                                if token:
                                    yield token
                            except json.JSONDecodeError:
                                logger.warning("Некорректная строка в стриме: %s", line)
            except Exception as e:
                logger.error(f"Ошибка стрима Ollama: {e}")
                raise ProviderError(f"Ollama стрим недоступен: {e}")

        # Возвращаем результат вызова внутреннего генератора
        return _stream_tokens() 