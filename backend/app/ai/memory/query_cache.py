import os 
import asyncio
from mem0 import Memory

from backend.app.core.config import settings
from backend.app.core.logger import logger

class QueryCache:
    def __init__(self, collection_name: str = "query_cache"):
        self.collection_name = collection_name
        self._memory = self._create_memory(collection_name)
    
    def _create_memory(self, collection_name: str) -> Memory:
        provider = getattr(settings, 'MEM0_LLM_PROVIDER', 'ollama')
        if provider == "ollama":
            llm_config = {
                "provider": "ollama",
                "config": {
                    "api_key": "ollama",
                    "model": settings.MEM0_LLM_MODEL,
                    "ollama_base_url": getattr(settings, 'MEM0_LLM_API_BASE', 'http://localhost:11434'),
                }
            }
        else:
            llm_config = {
                "provider": "gemini",
                "config": {
                    "api_key": settings.GEMINI_API_KEY,
                    "model": settings.MEM0_LLM_MODEL
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
                    "path": os.path.join(os.getcwd(), "chroma_db_mem0"),
                }
            }
        }
        return Memory.from_config(config)  
    async def get(self, user_id: str, query: str, threshold: float = 0.35):
        try:
            results = await asyncio.to_thread(
            self._memory.search, query, filters={"user_id": user_id}, limit=1
)
            
            if results and results.get('results'):
                best = results['results'][0]
                score = best.get('score', 0)
                logger.info(f"QueryCache best score: {score} (threshold: {threshold})")
                if score >= threshold:
                    logger.debug(f"QueryCache hit: {query[:50]}...")
                    return best.get('metadata', {}).get('response')
                else:
                    logger.info(f"QueryCache score too low: {score}")
            else:
                logger.info(f"QueryCache miss (no results): {query[:50]}...")
        except Exception as e:
            logger.warning(f"QueryCache search error: {e}")
        return None
    async def set(self, user_id: str, query: str, response: str):
            """Сохраняет запрос и соответствующий ответ."""
            try:
                await asyncio.to_thread(
                    self._memory.add,
                    query,
                    user_id=user_id,
                    metadata = {'response': response}

                )
                logger.debug(f"fQueryCache set: {query[:50]}...")
            except Exception as e :
                logger.warning(f"QueryCache set error{e}")
query_cache = QueryCache()

                    


        