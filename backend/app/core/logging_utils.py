import time
from functools import wraps
from typing import Callable, Any

# Используем единый настроенный логгер проекта
from backend.app.core.logger import logger

def log_execution_time(func: Callable) -> Callable:
    """
    Декоратор для логирования времени выполнения синхронной функции
    в миллисекундах. Уровень логирования: DEBUG.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                f"Function '{func.__name__}' executed in {elapsed_ms:.2f} ms",
                extra={"function": func.__name__, "duration_ms": elapsed_ms}
            )
    return wrapper