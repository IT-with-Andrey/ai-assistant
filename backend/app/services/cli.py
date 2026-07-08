import os
from backend.app.core.logger import logger
from backend.app.middlewares.base import ChatContext
from backend.app.ai.orchestrator_factory import create_chat_orchestrator
from backend.app.database.connection import AsyncSessionLocal
from dotenv import load_dotenv
import asyncio
import sys
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="mem0")
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="google.genai")
load_dotenv()
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../..')))


warnings.filterwarnings(
    "ignore", message=".*get_sentence_embedding_dimension.*")


async def main():
    logger.info("Запуск CLI-assistant")

    async with AsyncSessionLocal() as db:
        try:
            while True:
                user_input = input("You")
                if user_input == "exit":
                    break
                logger.debug('Получен ввод от пользователя')
                orchestrator = create_chat_orchestrator(db)
                ctx = ChatContext(user_input=user_input,
                                  user_id='default_user')
                ctx = await orchestrator.run(ctx)
                await db.commit()
                print(f'AI: {ctx.response or ""}')
        finally:
            logger.info("Сессия БД успешно закрыта, выход из CLI")

if __name__ == "__main__":
    asyncio.run(main())
