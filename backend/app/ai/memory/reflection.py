import hashlib
import time
import asyncio
from typing import Optional
from backend.app.ai.providers.base import BaseLLMProvider
from backend.app.ai.memory.episodic import EpisodicMemory
from backend.app.core.logger import logger

class ReflectionLayer:
    def __init__(self, llm_provider: BaseLLMProvider, memory_orchestrator, episodic_memory: EpisodicMemory):
        self.llm = llm_provider
        self.memory = memory_orchestrator
        self.episodic = episodic_memory
        # Простой кэш для рефлексий: ключ -> (timestamp, текст)
        self._reflection_cache: dict[str, tuple[float, str]] = {}
        self._cache_lock = asyncio.Lock()
        self._cache_ttl = 3600  # 1 час

    async def reflect(self, user_id: str, persona_id: str, period: str = "daily") -> Optional[str]:
        """Собирает события за период и создаёт сжатое резюме."""
        cache_key = f"{user_id}|{persona_id}|{period}"
        async with self._cache_lock:
            if cache_key in self._reflection_cache:
                ts, cached_text = self._reflection_cache[cache_key]
                if time.time() - ts < self._cache_ttl:
                    logger.debug("ReflectionLayer: использован кэш рефлексии")
                    return cached_text
                else:
                    del self._reflection_cache[cache_key]

        events = await self.episodic.get_recent_events(user_id, persona_id, limit=50)
        if not events:
            logger.debug("ReflectionLayer: нет событий для рефлексии")
            return None

        # Формируем текстовую сводку событий
        events_text = "\n".join(
            f"[{e.get('metadata', {}).get('event_type', '?')}] {e.get('text', '')[:200]}"
            for e in events if isinstance(e, dict)
        )

        prompt = f"""Ты — анализатор долговременной памяти. Изучи список событий за {period} и напиши сжатый отчёт (3-5 предложений) о действиях, решениях и новых знаниях о Создателе. Пиши от третьего лица, используй "Создатель".

События:
{events_text}

Отчёт:"""

        try:
            summary = await self.llm.generate_response([{"role": "user", "content": prompt}])
            if not summary:
                raise ValueError("Пустой ответ от LLM")
            # Сохраняем резюме в семантическую память
            await self.memory.add_user_memory(
                user_id,
                text=f"[{period} reflection] {summary.strip()}",
                persona_id=persona_id,
                metadata={"type": "reflection", "period": period}
            )
            async with self._cache_lock:
                self._reflection_cache[cache_key] = (time.time(), summary.strip())
            logger.info(f"ReflectionLayer: {period} отчёт создан")
            return summary.strip()
        except Exception as e:
            logger.error(f"ReflectionLayer: ошибка при создании отчёта: {e}")
            return None