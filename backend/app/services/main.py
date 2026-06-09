import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="mem0")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.database.connection import get_db
from backend.app.middlewares.base import ChatContext
from backend.app.ai.orchestrator_factory import create_chat_orchestrator
from backend.app.core.logger import logger
from backend.app.ai.orchestrator_factory import create_streaming_orchestrator


app = FastAPI(title="AI Assistant Persona API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"server": "running"}

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"

@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest, 
    background_tasks: BackgroundTasks, # Добавляем фоновые задачи для стрима
    db: AsyncSession = Depends(get_db)
):
    """Стриминговый эндпоинт с полной поддержкой памяти в фоновом режиме."""
    logger.info(f"Получен стрим-запрос от пользователя {request.user_id}")
    
    # Собираем оркестратор через единую фабрику
    orchestrator = create_streaming_orchestrator(db)
    ctx = ChatContext(user_input=request.message, user_id=request.user_id)
    
    try:
        ctx = await orchestrator.run(ctx)
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка выполнения оркестратора в стриме: {e}",exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка ИИ-конвейера")

    if not ctx.response_stream:
        await db.commit()
        raise HTTPException(status_code=500, detail="Провайдер не вернул стрим-данные")

    async def event_generator():
        success = True
        logger.debug("event_generator: начал передачу стрима")
        try:
            async for chunk in ctx.response_stream:
                yield f"data: {chunk}\n\n"
        except Exception as e:
            success = False
            logger.error(f"Ошибка во время передачи стрима пользователю: {e}", exc_info=True)
        finally:
            if success:
                await db.commit()
                logger.debug("event_generator: транзакция закоммичена")
            else:
                await db.rollback()
                logger.debug("event_generator: транзакция откачена")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/chat")
async def chat_regular(
    request: ChatRequest, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession  = Depends(get_db)
):
    """Обычный синхронный эндпоинт (для тестов/интеграций) через ту же фабрику."""
    orchestrator = create_chat_orchestrator(db, background_tasks=background_tasks)
    ctx = ChatContext(user_input=request.message, user_id=request.user_id)
    
    try:
        ctx = await orchestrator.run(ctx)
        await db.commit()
        return {"response": ctx.response or "Модель не вернула текстовый ответ."}
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка в синхронном чате: {e}")
        raise HTTPException(status_code=500, detail=str(e))