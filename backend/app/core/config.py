from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application-wide settings loaded from .env and environment."""
    AI_MODEL: str = "gemma4:31b-cloud"
    OLLAMA_HOST: str = "http://localhost:11434"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_assistant_db"
    OPENROUTER_API: str = ""
    OLLAMA_API_KEY: str = ""
    DEFAULT_USER_ID: str = "default_user"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

# Singleton instance to be imported throughout the project.
settings = Settings()