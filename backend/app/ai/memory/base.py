from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseVectorMemory(ABC):
    """Интерфейс для долговременной семантической памяти (Факты)"""
    @abstractmethod
    async def add_memory(self, user_id: str, text: str, metadata: Dict[str, Any] = None, persona_id: str = None) -> None:
        pass

    @abstractmethod
    async def search_memories(self, user_id: str, query: str, limit: int = 5, persona_id: str = None) -> List[str]:
        pass

    @abstractmethod
    async def get_all_memories(self, user_id: str, persona_id: str = None) -> List[str]:
        pass

class BaseHistoryPruner(ABC):
    @abstractmethod
    def prune(self, history: List[Dict[str, Any]], max_limit: int) -> List[Dict[str, Any]]:
        pass

class BaseMemoryOptimizer(ABC):
    @abstractmethod
    async def optimize(self, user_id: str) -> None:
        pass