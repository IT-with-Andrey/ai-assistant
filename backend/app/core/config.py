import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "none"
os.environ["MEM0_TELEMETRY_DISABLED"] = "True"


class Settings(BaseSettings):
    """Application-wide settings loaded from .env and environment."""
    AI_MODEL: str = "gemma4:31b-cloud"
    OLLAMA_HOST: str = "http://localhost:11434"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_assistant_db"
    OPENROUTER_API: str = ""
    OLLAMA_API_KEY: str = ""
    DEFAULT_USER_ID: str = "default_user"
    GEMINI_API_KEY: str = ""   # <-- твой новый ключ
    GROK_API_KEY: str = ""     # <-- заготовка на будущее
    LLM_PROVIDER: str = "ollama"  # ollama / gemini / grok
    MEM0_LLM_MODEL: str = "gemini-2.5-flash-lite"
    MEM0_LLM_FALLBACK_MODELS: list[str] = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",        # чтобы не ругался на любые другие переменные
    }


settings = Settings()
