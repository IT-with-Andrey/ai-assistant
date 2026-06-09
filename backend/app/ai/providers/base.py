from abc import ABC, abstractmethod
from typing import List, Dict , AsyncGenerator

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass

    async def genetate_stream(self, messages: List[Dict[str,str]], **kwargs) ->AsyncGenerator[str, None]:
        """Генерирует ответ по частям (стриминг). Возвращает асинхронный генератор токенов.
        """
        pass