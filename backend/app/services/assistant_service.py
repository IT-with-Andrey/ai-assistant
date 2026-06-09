from sqlalchemy.orm import Session
from backend.app.core.logger import logger
from backend.app.database.repository import MessageRepository
from backend.app.ai.persona_manager import PersonaManager
from backend.app.ai.orchestrator_factory import app_container, create_chat_orchestrator
from backend.app.middlewares.base import ChatContext

# Получаем готовый оркестратор из фабрики
def get_orchestrator(db: Session):
    return create_chat_orchestrator(db)

async def chat(user_input: str, db: Session, user_id: str = 'default_user') -> str:
    # Используем фабрику для создания чистого конвейера (уже без Олламы)
    orchestrator = get_orchestrator(db)
    
    ctx = ChatContext(user_input=user_input, user_id=user_id, db=db)

    try:
        ctx = await orchestrator.run(ctx)
        db.commit()
        return ctx.response or ""
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка в цепочке middleware: {e}")
        return "Извините, произошла внутренняя ошибка системы."

