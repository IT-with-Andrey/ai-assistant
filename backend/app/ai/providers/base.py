from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator

class BaseLLMProvider(ABC):
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Генерирует полный ответ одной строкой."""
        pass

    @abstractmethod
    async def generate_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Генерирует ответ по частям (стриминг). 
        Обязателен к реализации во всех наследниках.
        """
        pass