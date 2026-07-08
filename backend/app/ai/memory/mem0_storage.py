import os
import asyncio
import hashlib
from typing import Dict, List, Any
from mem0 import Memory
from backend.app.core.config import settings
from backend.app.ai.memory.base import BaseVectorMemory
from backend.app.core.logger import logger

os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["MEM0_TELEMETRY_DISABLED"] = "true"

class Mem0StorageProvider(BaseVectorMemory):
    def __init__(self):
        self.current_model = settings.MEM0_LLM_MODEL
        self._memory_cache: Dict[str, Memory] = {}

    def _get_collection_name(self, user_id: str, persona_id: str = None) -> str:
        short_id = user_id[:8] if len(user_id) <= 12 else hashlib.md5(user_id.encode()).hexdigest()[:8]
        if persona_id:
            return f'mem0_{short_id}_{persona_id}'
        return f'mem0_{short_id}_global'

    def _get_or_create_memory(self, collection_name: str) -> Memory:
        if collection_name not in self._memory_cache:
            logger.debug(f'Create new collection: {collection_name}')
            self._memory_cache[collection_name] = self._create_memory(self.current_model, collection_name=collection_name)
        return self._memory_cache[collection_name]

    def _chroma_db_path(self) -> str:
        return os.path.join(os.getcwd(), "chroma_db_mem0")

    def _create_memory(self, model: str, collection_name: str = "mem0_memory") -> Memory:
        provider = getattr(settings, 'MEM0_LLM_PROVIDER', 'gemini')
        if provider == "ollama":
            llm_config = {
                "provider": "ollama",
                "config": {
                    "api_key": "ollama",
                    "model": model,
                    "ollama_base_url": getattr(settings, 'MEM0_LLM_API_BASE', 'http://localhost:11434'),
                }
            }
        else:
            llm_config = {
                "provider": "gemini",
                "config": {
                    "api_key": settings.GEMINI_API_KEY,
                    "model": model
                }
            }
        config = {
            "llm": llm_config,
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": collection_name,
                    "path": self._chroma_db_path(),
                }
            }
        }
        return Memory.from_config(config)

    async def add_memory(self, user_id: str, text: str, metadata: Dict[str, Any] = None, persona_id: str = None) -> Any:
        collection_name = self._get_collection_name(user_id, persona_id)
        memory = self._get_or_create_memory(collection_name)
        try:
            logger.debug(f"Mem0.add_memory START: user={user_id}, persona={persona_id}, text='{text[:100]}...'")
            result = await asyncio.to_thread(memory.add, text, user_id=user_id, metadata=metadata, infer=False)
            logger.debug(f"Mem0.add_memory RESULT: {result}")
            return result
        except Exception as e:
            logger.error(f"Mem0.add_memory ERROR: {e}")
            raise

    async def get_all_memories(self, user_id: str, persona_id: str = None) -> list[str]:
        collection_name = self._get_collection_name(user_id, persona_id)
        memory = self._get_or_create_memory(collection_name)
        try:
            raw = await asyncio.to_thread(memory.get_all, filters={"user_id": user_id})
            logger.debug(f"Mem0.get_all_memories: user={user_id}, persona={persona_id}, raw: {raw}")
            memories = raw.get('results', []) if isinstance(raw, dict) else []
            return [m.get('memory', '') for m in memories if isinstance(m, dict)]
        except Exception as e:
            logger.error(f"Mem0.get_all_memories ERROR: {e}")
            return []

    async def search_memories(self, user_id: str, query: str, limit: int = 3, persona_id: str = None) -> List[str]:
        collection_name = self._get_collection_name(user_id, persona_id)
        memory = self._get_or_create_memory(collection_name)
        try:
            raw = await asyncio.to_thread(memory.search, query, filters={'user_id': user_id}, limit=limit)
            logger.debug(f"Mem0.search_memories: query='{query}', persona={persona_id}, raw: {raw}")
            results = raw.get('results', []) if isinstance(raw, dict) else []
            return [r.get('memory', '') for r in results if isinstance(r, dict) and r.get('memory')]
        except Exception as e:
            logger.error(f"Mem0.search_memories ERROR: {e}")
            return []