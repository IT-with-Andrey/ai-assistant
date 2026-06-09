
from abc import ABC , abstractmethod
from typing import List, Dict, Any


class BaseVectorMemory(ABC):
    """Интерфейс для долговременной семантической памяти (Факты)"""
    @abstractmethod
    async def add_memory(self, user_id: str , text: str , metadata: Dict[str, Any] = None) -> None:
        pass

    @abstractmethod
    async def search_memories(self , user_id: str , query: str , limit: int = 5 ) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_all_memories(self, user_id: str) -> List[str]:
        pass
 
class BaseHistoryPruner(ABC):
     """Интерфейс для контроля и прунинга (обрезки) контекста истории диалогаможно удалять самые старые, 
     можно оценивать важность и вырезать середину. 
     Этот интерфейс позволяет менять стратегию без переделки основного кода.
     """  
     @abstractmethod
     def prune(self , history: List[Dict[str, Any]] , max_limit: int)-> List[Dict[str , Any]]:
         pass 

class BaseMemoryOptimizer(ABC):
    """Интерфейс для фоновой оптимизации («сна») памяти"""
    @abstractmethod
    async def optimize(self , user_id: str) -> None:
        pass
