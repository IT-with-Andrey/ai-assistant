
import logging
import sys

def setup_logger(name: str = 'assistant' , level: int = logging.DEBUG) -> logging.Logger:
     """Настраивает и возвращает логгер с заданным именем и уровнем."""

     logger = logging.getLogger(name)

     # Чтобы не дублировать обработчики при повторных вызовах
     if logger.handlers:
          return logger
     

     logger.setLevel(level)


        # Формат: время - имя - уровень - сообщени

     formatter = logging.Formatter(
          "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
          datefmt="%Y-%m-%d %H:%M:%S"
          
     )

     # Вывод в консоль

     console_handler = logging.StreamHandler(sys.stdout)

     console_handler.setFormatter(formatter)

     logger.addHandler(console_handler)
     # Опционально: вывод в файл (раскомментируй, если хочешь сохранять логи)
    # file_handler = logging.FileHandler("assistant.log", encoding="utf-8")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

     return logger

logger = setup_logger()