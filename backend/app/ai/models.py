from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class Fact(BaseModel):
    """Единичный факт о пользователе в формате key-value."""
    key: str = Field(description="Тип факта: name, goal, interest, preference, fact")
    value: str = Field(description="Содержимое факта")

class FactsResponse(BaseModel):
    """
    Контейнер для списка фактов.
    Может использоваться в API или для валидации упакованного ответа.
    """
    facts: list[Fact] = Field(default_factory=list)

class Settings(BaseSettings):
    """Настройки AI-модуля, загружаемые из переменных окружения."""
    model_name: str = "llama3"
    ollama_host: str = "http://localhost:11434"

    class Config:
        env_file = ".env"