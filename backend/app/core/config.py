

from dotenv import load_dotenv

import os

load_dotenv()

API_KEY = os.getenv('OPENROUTER_API')

MODEL = os.getenv("MODEL")
