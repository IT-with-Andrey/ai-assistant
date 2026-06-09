import os 
import asyncio
from typing import Dict, List, Any
from mem0 import Memory
from backend.app.core.config import settings
from backend.app.ai.memory.base import BaseVectorMemory
from backend.app.core.logger import logger

os.environ["MEM0_TELEMETRY_DISABLED"] = 'true'

class Mem0StorageProvider(BaseVectorMemory):
    def __init__(self):
        self.models = [settings.MEM0_LLM_MODEL] + settings.MEM0_LLM_FALLBACK_MODELS
        self.current_model = settings.MEM0_LLM_MODEL
        self.memory = self._create_memory(self.current_model)

    def _create_memory(self, model: str) -> Memory:
        config = {
            "llm": {
                "provider": "gemini",
                "config": {
                    "api_key": settings.GEMINI_API_KEY,
                    "model": model
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "mem0_memory",
                    "path": os.path.join(os.getcwd(), "chroma_db_mem0")
                }
            }
        }
        return Memory.from_config(config)

    def switch_model(self, model_name: str):
        """Горячая замена модели памяти."""
        if model_name != self.current_model:
            logger.info(f"Mem0 переключается на модель: {model_name}")
            self.current_model = model_name
            self.memory = self._create_memory(model_name)

    async def _try_with_fallback(self, func, *args, **kwargs):
        """Перебирает модели, пока не получит успешный результат."""
        last_error = None
        for model in self.models:
            try:
                if model != self.current_model:
                    self.switch_model(model)
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Mem0 ошибка с моделью {model}: {e}")
                last_error = e
        raise last_error

    async def add_memory(self, user_id: str, text: str, metadata: Dict[str, Any] = None) -> Any:
        async def _add():
            logger.debug(f"Mem0.add_memory START: user={user_id}, text='{text[:100]}...'")
            result = await asyncio.to_thread(self.memory.add, text, user_id=user_id, metadata=metadata)
            logger.debug(f"Mem0.add_memory RESULT: {result}")
            return result
        return await self._try_with_fallback(_add)
    
    async def get_all_memories(self, user_id: str) -> list[str]:
        async def _get_all():
            raw = await asyncio.to_thread(self.memory.get_all, filters={"user_id": user_id})
            logger.debug(f"Mem0.get_all_memories: user={user_id}, сырые данные: {raw}")
            memories = raw.get('results', []) if isinstance(raw, dict) else []
            facts = []
            for m in memories:
                if isinstance(m, dict):
                    facts.append(m.get('text', ''))
            return facts
        return await self._try_with_fallback(_get_all)

    async def search_memories(self, user_id: str, query: str, limit: int = 3) -> List[str]:
        async def _search():
            raw = await asyncio.to_thread(self.memory.search, query, filters={'user_id': user_id}, limit=limit)
            logger.debug(f"Mem0.search_memories: query='{query}', сырые результаты: {raw}")
            results = raw.get('results', []) if isinstance(raw, dict) else []
            if not results:
                return []
            relevant_facts = []
            for r in results:
                fact = r.get('text', '') if isinstance(r, dict) else str(r)
                if fact:
                    relevant_facts.append(fact)
            return relevant_facts
        return await self._try_with_fallback(_search)