from backend.app.ai.memory.base import BaseMemoryOptimizer
from backend.app.core.logger import logger

class MockMemoryOptimizer(BaseMemoryOptimizer):
    """Заглушка для фонового агента-санитара. Сюда мы позже прикрутим DreamOptimizer."""
    async def optimize(self, user_id: str) -> None:
        # Пока просто логируем, код готов к расширению
        logger.debug(f"Фоновая оптимизация памяти запущена для пользователя: {user_id}")