from typing import List, Dict, Any

from backend.app.ai.memory.base import BaseVectorMemory, BaseHistoryPruner, BaseMemoryOptimizer


class MemoryOrchestrator:
    """
    Масштабируемый координатор памяти уровня Enterprise.
    Управляет долгосрочной, краткосрочной памятью и оптимизацией через интерфейсы.
    """

    def __init__(
        self,
        vector_memory: BaseVectorMemory,
        pruner: BaseHistoryPruner,
        optimizer: BaseMemoryOptimizer
    ):
        self.vector_memory = vector_memory
        self.pruner = pruner
        self.optimizer = optimizer

    async def add_user_memory(self, user_id: str, text: str):
        return await self.vector_memory.add_memory(user_id, text)
    
    async def get_user_fact(self, user_id: str) -> List[str]:
        return await self.vector_memory.get_all_memories(user_id)
    
    async def search_relevant_facts(self, user_id: str, query: str, limit: int = 3) -> str:
        facts = await self.vector_memory.search_memories(user_id, query, limit)
        if not facts:
            return ""
        return "\n".join([f'-{fact}' for fact in facts])
    
    async def get_clean_context(self, user_id: str, query: str, raw_history: List[Any], max_history_bytes: int = 30000) -> Dict[str, Any]:
        facts_list = await self.vector_memory.search_memories(user_id, query, limit=3)
        safe_history = self.pruner.prune(raw_history, max_bytes=max_history_bytes)
        return {
            "relevant_facts": "\n".join([f'- {f}' for f in facts_list]),
            "safe_history": safe_history
        }

# ⚠️ ВСЕ ЛИШНИЕ ИНИЦИАЛИЗАЦИИ ОТСЮДА УБРАНЫ.
# Теперь сборка оркестратора происходит строго внутри фабрики AppContainer в единственном экземпляре!