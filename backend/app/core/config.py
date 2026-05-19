
# Она нужна, чтобы загрузить переменные из файла .env в системные переменные окружения.
from dotenv import load_dotenv

import os


# Вызываем load_dotenv() — она ищет файл .env в корне проекта,
# читает его и делает все переменные оттуда доступными через os.getenv().
load_dotenv()

API_KEY = os.getenv('OPENROUTER_API')

MODEL = os.getenv("MODEL")


