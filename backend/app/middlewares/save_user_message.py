import asyncio
from .base import BaseMiddleware, ChatContext
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.repository import MessageRepository

class SaveUserMessageMiddleware(BaseMiddleware):
    def __init__(self, db: AsyncSession):
        self.repo = MessageRepository(db)
    async def process(self, ctx: ChatContext) -> ChatContext:
        await self.repo.save(role='user', content=ctx.user_input, user_id=ctx.user_id)
        return ctx