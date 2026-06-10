
import os 
import json
import sqlite3
import asyncio
import time
from typing import Dict, List, Any
from mem0 import Memory
from backend.app.core.config import settings
from backend.app.ai.memory.base import BaseVectorMemory
from backend.app.core.logger import logger

os.environ["CHROMA_TELEMETRY_DISABLED"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

_DEBUG_LOG_PATH = os.path.join(os.getcwd(), "debug-6197b6.log")


def _agent_debug_log(location: str, message: str, data: dict, hypothesis_id: str, run_id: str = "pre-fix") -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "6197b6",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion


class Mem0StorageProvider(BaseVectorMemory):
    def __init__(self):
        self.models = [settings.MEM0_LLM_MODEL] + settings.MEM0_LLM_FALLBACK_MODELS
        self.current_model = settings.MEM0_LLM_MODEL
        self._memory_cache: Dict[str, Memory] = {}
        self._current_global_memory = self._create_memory(self.current_model, collection_name="mem0_memory_global")

    def _get_collection_name(self, user_id: str , persona_id:str = None) -> str:
        if persona_id:
            return f'mem0_memory_{user_id}_{persona_id}'
        return f'mem0_memory_{user_id}_global'
    
    def _get_or_create_memory(self, collection_name: str) -> Memory:
        if collection_name not in self._memory_cache:
            logger.debug(f'Creat new collection{collection_name}')
            self._memory_cache[collection_name] = self._create_memory(self.current_model,collection_name=collection_name)
        return self._memory_cache[collection_name]



    def _chroma_db_path(self) -> str:
        return os.path.join(os.getcwd(), "chroma_db_mem0")

    def _repair_chroma_db_if_needed(self, path: str) -> int:
        """Fix ChromaDB 0.5.x incompatibility with legacy empty collection configs."""
        sqlite_path = os.path.join(path, "chroma.sqlite3")
        if not os.path.exists(sqlite_path):
            _agent_debug_log(
                "mem0_storage.py:_repair_chroma_db_if_needed",
                "Chroma sqlite db not found",
                {"path": path, "sqlite_path": sqlite_path},
                "H3",
            )
            return 0

        conn = sqlite3.connect(sqlite_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, config_json_str FROM collections")
            rows = cur.fetchall()
            broken_collections = []
            for collection_id, name, config_json in rows:
                parsed = {}
                if config_json:
                    try:
                        parsed = json.loads(config_json)
                    except json.JSONDecodeError:
                        parsed = {"__invalid_json__": True}
                if config_json in (None, "", "{}") or (parsed and "_type" not in parsed):
                    broken_collections.append(
                        {"id": collection_id, "name": name, "config_json_str": config_json}
                    )

            _agent_debug_log(
                "mem0_storage.py:_repair_chroma_db_if_needed",
                "Scanned Chroma collections",
                {
                    "path": path,
                    "total_collections": len(rows),
                    "broken_collections": broken_collections,
                    "chromadb_version_hint": "0.5.x expects _type in config_json_str",
                },
                "H1",
            )

            if not broken_collections:
                return 0

            cur.execute(
                "UPDATE collections SET config_json_str = NULL "
                "WHERE config_json_str = '{}' OR config_json_str = ''"
            )
            repaired = cur.rowcount
            conn.commit()

            _agent_debug_log(
                "mem0_storage.py:_repair_chroma_db_if_needed",
                "Repaired legacy Chroma collection configs",
                {"repaired_rows": repaired},
                "H1",
            )
            return repaired
        finally:
            conn.close()

    def _create_memory(self, model: str, collection_name: str ="mem0_memory") -> Memory:
        chroma_path = self._chroma_db_path()
        _agent_debug_log(
            "mem0_storage.py:_create_memory",
            "Creating Mem0 memory instance",
            {"collection_name": collection_name, "chroma_path": chroma_path, "model": model},
            "H3",
        )
        repaired = self._repair_chroma_db_if_needed(chroma_path)
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
        else:  # gemini (старое поведение по умолчанию)
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
                    "path": chroma_path,
                }
            }
        }
        try:
            memory = Memory.from_config(config)
            _agent_debug_log(
                "mem0_storage.py:_create_memory",
                "Mem0 memory initialized successfully",
                {"collection_name": collection_name, "repaired_rows": repaired},
                "H1",
            )
            return memory
        except Exception as exc:
            _agent_debug_log(
                "mem0_storage.py:_create_memory",
                "Mem0 memory initialization failed",
                {
                    "collection_name": collection_name,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "repaired_rows": repaired,
                },
                "H1",
            )
            raise

    def switch_model(self, model_name: str):
        """Горячая замена модели памяти."""
        if model_name != self.current_model:
            logger.info(f"Mem0 переключается на модель: {model_name}")
            self.current_model = model_name
            for collection_name , memory in list(self._memory_cache.items()):
                self._memory_cache[collection_name] = self._create_memory(model_name, collection_name=collection_name)
            self._current_global_memory = self._create_memory(model_name , collection_name="mem0_memory_global")

            

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

    async def add_memory(self, user_id: str, text: str, metadata: Dict[str, Any] = None, persona_id: str =None) -> Any:
        
            collection_name = self._get_collection_name(user_id , persona_id)
            memory = self._get_or_create_memory(collection_name)
            async def _add():
                    logger.debug(f"Mem0.add_memory: user={user_id}, persona={persona_id}, text='{text[:100]}...'")
                    result = await asyncio.to_thread(memory.add, text, user_id=user_id, metadata=metadata)
                    logger.debug(f"Mem0.add_memory RESULT: {result}")
                    return result
            return await self._try_with_fallback(_add)
                
    async def get_all_memories(self, user_id: str, persona_id: str=None) -> list[str]:
        collection_name = self._get_collection_name(user_id , persona_id)
        memory = self._get_or_create_memory(collection_name)
        async def _get_all():
            raw = await asyncio.to_thread(memory.get_all, filters={"user_id": user_id})
            logger.debug(f"Mem0.get_all_memories: user={user_id}, сырые данные: {raw}")
            memories = raw.get('results', []) if isinstance(raw, dict) else []
            facts = []
            for m in memories:
                if isinstance(m, dict):
                    facts.append(m.get('text', ''))
            return facts
        return await self._try_with_fallback(_get_all)

    async def search_memories(self, user_id: str, query: str, limit: int = 3, persona_id: str = None) -> List[str]:
        collection_name = self._get_collection_name(user_id, persona_id)
        memory = self._get_or_create_memory(collection_name)

        async def _search():
            
            raw = await asyncio.to_thread(memory.search, query, filters={'user_id': user_id}, limit=limit)
            logger.debug(f"Mem0.search_memories: query='{query}', сырые результаты: {raw}")
            results = raw.get('results', []) if isinstance(raw, dict) else []
            relevant_facts = []
            for r  in results:
                fact = r.get('memory', r.get('text',''))
                if fact:
                    relevant_facts.append(fact)
            return relevant_facts
        return await self._try_with_fallback(_search)