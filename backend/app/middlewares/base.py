from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Optional, AsyncGenerator

class ChatContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_input: str
    user_id: str = "default_user"
    
    response: Optional[str] = None
    should_stop: bool = False
    history: List[Dict[str, str]] = Field(default_factory=list)
    facts: Optional[str] = None
    llm_context: List[Dict[str, str]] = Field(default_factory=list)
    # Новые поля для стриминга и ошибок
    response_stream: Optional[AsyncGenerator[str, None]] = None
    error: Optional[str] = None

class BaseMiddleware(ABC):
    @abstractmethod
    async def process(self, ctx: ChatContext) -> ChatContext:
        pass