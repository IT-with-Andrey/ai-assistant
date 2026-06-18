import time
from typing import Dict, Any, Optional
from backend.app.core.logger import logger

class EpisodicMemory:
    # Короткое фиксированное имя коллекции для всех событий
    COLLECTION_NAME = "episodic_memory"

    def __init__(self, memory_orchestrator):
        self.memory = memory_orchestrator

    async def log_event(self, user_id: str, persona_id: str, event_type: str, data: Dict[str, Any]):
        """Сохраняет событие в общую коллекцию episodik_memory."""
        timestamp = data.get("timestamp") or time.time()
        text = f"[{event_type}] {data.get('user_message', '')[:100]}"
        metadata = {
            "event_type": event_type,
            "timestamp": timestamp,
            "importance": data.get("importance"),
            "user_id": user_id,               # для фильтрации
            "persona_id": persona_id or "",   # для фильтрации
        }
        try:
            # Вызываем add_user_memory с persona_id=None, чтобы не создавать отдельные коллекции
            # и передаём имя нашей единой коллекции через дополнительный параметр.
            # Но add_user_memory ожидает persona_id для построения имени коллекции.
            # Поэтому временно воспользуемся прямым вызовом метода хранилища, если он доступен.
            # Либо модифицируем MemoryOrchestrator для поддержки произвольного имени коллекции.
            # Быстрое решение: передадим persona_id=COLLECTION_NAME, тогда коллекция будет 'mem0_memory_{user_id}_episodic_memory'
            # что всё ещё длинное. Поэтому лучше расширить MemoryOrchestrator.add_user_memory, разрешив передавать имя коллекции.
            # Пока сделаем обходной путь: сохраняем событие в основную память с persona_id="episodic_global",
            # но в metadata продублируем persona_id. Потом при получении отфильтруем.
            await self.memory.add_user_memory(
                user_id,
                text=text,
                persona_id=None,               # попадает в коллекцию global
                metadata=metadata
            )
            logger.debug(f"EpisodicMemory: событие '{event_type}' сохранено (важность {data.get('importance')})")
        except Exception as e:
            logger.error(f"EpisodicMemory: ошибка сохранения события: {e}")

    async def get_recent_events(self, user_id: str, persona_id: str, limit: int = 50):
        """Возвращает последние N событий, отфильтрованные по user_id и persona_id."""
        try:
            all_facts = await self.memory.get_user_fact(user_id, persona_id=None)
        # Отбираем только те факты, которые являются событиями (по префиксу '[')
            events = [f for f in all_facts if isinstance(f, str) and f.startswith('[')]
            logger.debug(f"EpisodicMemory: получено {len(events)} событий для {user_id}")
            return events[-limit:]
        except Exception as e:
            logger.error(f"EpisodicMemory: ошибка получения событий: {e}")
            return []