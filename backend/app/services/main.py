import uuid
import warnings

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.connection import get_db
from backend.app.database.repository import MessageRepository
from backend.app.middlewares.base import ChatContext
from backend.app.ai.orchestrator_factory import create_chat_orchestrator, create_streaming_orchestrator
from backend.app.ai.personas import PERSONAS
from backend.app.ai.orchestrator_factory import app_container
from backend.app.core.logger import logger

warnings.filterwarnings("ignore", category=FutureWarning, module="mem0")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")

app = FastAPI(title="AI Assistant Persona API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"server": "running"}

# --- Модели запросов ---
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    persona_id: str | None = None

class InitChatRequest(BaseModel):
    session_id: str
    persona_id: str = "default"

# --- Стриминг ---
@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Получен стрим-запрос от пользователя {request.user_id}")
    orchestrator = create_streaming_orchestrator(db, background_tasks=background_tasks )
    ctx = ChatContext(user_input=request.message, user_id=request.user_id, persona_id=request.persona_id)

    try:
        ctx = await orchestrator.run(ctx)
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка выполнения оркестратора в стриме: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка ИИ-конвейера")

    if not ctx.response_stream:
        if ctx.response:  # ← команда вернула ответ
            async def _command_stream():
                yield ctx.response
            ctx.response_stream = _command_stream()
        else:
            await db.commit()
            raise HTTPException(status_code=500, detail="Провайдер не вернул стрим-данные")

    async def event_generator():
        success = True
        assistant_text = ""  # ← накапливаем ответ
        logger.debug("event_generator: начал передачу стрима")
        try:
            async for chunk in ctx.response_stream:
                assistant_text += chunk
                yield f"data: {chunk}\n\n"
        except Exception as e:
            success = False
            logger.error(f"Ошибка во время передачи стрима пользователю: {e}", exc_info=True)
        finally:
            if success and assistant_text:  # ← сохраняем только если есть текст
                try:
                    await MessageRepository(db).save(
                        role='assistant',
                        content=assistant_text,
                        user_id=request.user_id
                    )
                    await db.commit()
                    logger.debug("event_generator: ответ ассистента сохранён и транзакция закоммичена")
                except Exception as e:
                    await db.rollback()
                    logger.error(f"event_generator: ошибка сохранения ответа: {e}")
            elif success:
                await db.commit()  # ← пустой ответ, но коммитим user-сообщение
                logger.debug("event_generator: транзакция закоммичена (пустой ответ)")
            else:
                await db.rollback()
                logger.debug("event_generator: транзакция откачена")
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- Обычный чат ---
@app.post("/chat")
async def chat_regular(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    orchestrator = create_chat_orchestrator(db, background_tasks=background_tasks)
    ctx = ChatContext(user_input=request.message, user_id=request.user_id, persona_id=request.persona_id)

    try:
        ctx = await orchestrator.run(ctx)
        await db.commit()
        return {"response": ctx.response or "Модель не вернула текстовый ответ."}
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка в синхронном чате: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Инициализация чата ---
@app.post("/chats/init")
async def init_chat(request: InitChatRequest, db: AsyncSession = Depends(get_db)):
    if request.persona_id not in PERSONAS:
        request.persona_id = "default"

    persona = PERSONAS[request.persona_id]
    chat_id = str(uuid.uuid4())
    welcome = persona["welcome_message"]

    try:
        repo = MessageRepository(db)
        await repo.save(role="assistant", content=welcome, user_id=request.session_id)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка инициализации чата: {e}")

    # Сохраняем факт о выбранной роли в глобальную память (временно обёрнуто в try/except)
    try:
        await app_container.memory_orchestrator.add_user_memory(
            request.session_id,
            text=f"assistant_role: {request.persona_id}",
            persona_id=None
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения роли в память: {e}", exc_info=True)

    return {
        "status": "success",
        "chat_id": chat_id,
        "persona_id": request.persona_id,
        "display_name": persona["display_name"],
        "welcome_message": welcome
    }

