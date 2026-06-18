import json
import re
import hashlib
import time
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.ai.providers.base import BaseLLMProvider
from backend.app.ai.memory.episodic import EpisodicMemory
from backend.app.core.logger import logger


class ExtractedFact(BaseModel):
    fact: str = Field(description="Атомарный факт о создателе в третьем лице.")
    category: str = Field(
        description="Категория: 'biography', 'preferences', 'work', 'habits', 'relations', 'meta'")


class MemoryPayload(BaseModel):
    facts: List[ExtractedFact] = Field(default_factory=list)


class MemoryManager:
    IMPORTANCE_THRESHOLD = 6
    DEFAULT_IMPORTANCE = 5
    CACHE_TTL_SECONDS = 300

    def __init__(self, llm_provider: BaseLLMProvider, memory_orchestrator, episodic_memory: Optional[EpisodicMemory] = None):
        self.llm = llm_provider
        self.memory = memory_orchestrator
        self.episodic = episodic_memory
        # Кеш: ключ -> (timestamp, значение)
        self._importance_cache: Dict[str, tuple[float, int]] = {}
        self._facts_cache: Dict[str, tuple[float, list[ExtractedFact]]] = {}
        self._cache_lock = asyncio.Lock()

    def _make_cache_key(self, user_id: str, persona_id: str, user_message: str, assistant_response: str) -> str:
        """Уникальный ключ на основе содержимого сообщений."""
        raw = f"{user_id}|{persona_id}|{user_message}|{assistant_response}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _cache_get(self, cache_dict: dict, key: str) -> Optional[Any]:
        async with self._cache_lock:
            entry = cache_dict.get(key)
            if entry and (time.time() - entry[0]) < self.CACHE_TTL_SECONDS:
                return entry[1]
            elif entry:
                del cache_dict[key]  # Устарело удаляем
            return None

    async def _cache_set(self, cache_dict: dict, key: str, value: Any):
        async with self._cache_lock:
            cache_dict[key] = (time.time(), value)

    async def invalidate_cache(self):
        """Очищает весь кэш (может вызываться по команде)."""
        async with self._cache_lock:
            self._importance_cache.clear()
            self._facts_cache.clear()
            logger.info('MemoryManager: cache Полностью очищен ')

    async def assess_importance(self, user_message: str,
                                assistant_response: str,
                                user_id: str = 'default',
                                persona_id: str = None) -> int:
        cache_key = self._make_cache_key(
            user_id, persona_id, user_message, assistant_response)
        cached = await self._cache_get(self._importance_cache, cache_key)
        if cached is not None:
            logger.debug(
                "MemoryManager: Использован закешированный скоринг важности")
            return cached
        prompt = f"""Ты — аналитик подсистемы памяти персонального AI.
                        Оцени, насколько критично сохранить информацию из этого диалога в ДОЛГОВРЕМЕННУЮ память (биографию, привычки, цели создателя).

                        Шкала оценки (1-10):
                        - 1-3: Пустой разговор, приветствия, дежурные фразы, сиюминутный контекст.
                        - 4-5: Обсуждение общих тем, не касающихся личности создателя напрямую.
                        - 6-7: Важные детали, предпочтения, привычки, хобби, упоминание работы.
                        - 8-10: Критическая информация (имена близких, долгосрочные цели, важные решения).

                        [ДИАЛОГ]
                        Создатель: {user_message}
                        Ассистент: {assistant_response}

                        Выведи только ОДНО ЦЕЛОЕ ЧИСЛО от 1 до 10 в формате: <score>число</score>
                        """
        try:
            response = await self.llm.generate_response([{"role": "user", "content": prompt}])
            clean_response = response.strip()
            match = re.search(
                r'<score>(\d+)</score>', clean_response) or re.search(r'\b([1-9]|10)\b', clean_response)
            score = max(1, min(10, int(match.group(1)))
                        ) if match else self.DEFAULT_IMPORTANCE
            await self._cache_set(self._importance_cache, cache_key, score)
            return score
        except Exception as e:
            logger.exception(
                f"MemoryManager: Ошибка при оценке важности: {e}")
            return self.DEFAULT_IMPORTANCE

    async def extract_atomic_facts(self, user_message: str,
                                    assistant_response: str,
                                    user_id: str = "default",
                                    persona_id: str = None) -> List[ExtractedFact]:

        cache_key = self._make_cache_key(user_id, persona_id, user_message, assistant_response)
        cached = await self._cache_get(self._facts_cache, cache_key)
        if cached is not None:
            logger.debug("MemoryManager: Использованы закешированные факты")
            return cached

        prompt = f"""Ты — инжиниринг-модуль экстракции знаний. Твоя задача — извлечь новые стабильные факты о Создателе из текста диалога.
                Переформулируй их строго в третьем лице (используй "Создатель..."). 

                [ДИАЛОГ]
                Создатель: {user_message}
                Ассистент: {assistant_response}

                Выведи результат строго в формате JSON-массива объектов. Никакого другого текста, разметки или пояснений.
                Формат ответа:
                {{
                "facts": [
                    {{"fact": "Создатель переехал в Берлин в июне 2026 года.", "category": "biography"}},
                    {{"fact": "Создатель предпочитает строгую типизацию в Python.", "category": "preferences"}}
                ]
                }}
                """
        try:
            response = await self.llm.generate_response([{"role": "user", "content": prompt}])
            clean_json_str = response.strip()
            if "```" in clean_json_str:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_json_str, re.DOTALL)
                if json_match:
                    clean_json_str = json_match.group(1)
            data = json.loads(clean_json_str)
            payload = MemoryPayload(**data)
            await self._cache_set(self._facts_cache, cache_key, payload.facts)
            return payload.facts
        except Exception as e:
            logger.error(f"MemoryManager: Ошибка экстракции фактов или валидации JSON: {e}")
            return []

    async def process_memory_pipeline(self, user_id: str,
                                        persona_id: str,
                                        user_message: str,
                                        assistant_response: str):
        """Фоновый пайплайн обработки памяти."""
        try:
            importance = await self.assess_importance(user_message, assistant_response, user_id, persona_id)
            logger.debug(f"MemoryManager [Background]: Скоринг важности = {importance}")
            if self.episodic:
                await self.episodic.log_event(
                    user_id=user_id, persona_id=persona_id,
                    event_type="message",
                    data={"user_message": user_message[:100], "assistant_response": assistant_response[:100],
                          "importance": importance}
                )
            if importance >= self.IMPORTANCE_THRESHOLD:
                facts = await self.extract_atomic_facts(user_message, assistant_response, user_id, persona_id)
                for item in facts:
                    logger.info(f"MemoryManager: Сохранение нового факта ({item.category}): {item.fact}")
                    await self.memory.add_user_memory(
                        user_id=user_id,
                        text=item.fact,
                        persona_id=persona_id,
                        metadata={"importance": importance,
                                   "category": item.category,
                                    "raw_trigger": user_message[:100]}
                    )
        except Exception as e:
            logger.exception(f"MemoryManager: Критическая ошибка в фоновом пайплайне памяти: {e}")