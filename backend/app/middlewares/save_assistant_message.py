import asyncio
from .base import BaseMiddleware, ChatContext
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.repository import MessageRepository

class SaveAssistantMessageMiddleware(BaseMiddleware):
    def __init__(self, db: AsyncSession):
        self.repo = MessageRepository(db)
    async def process(self, ctx: ChatContext) -> ChatContext:
        if ctx.response:
            await self.repo.save(role='assistant', content=ctx.response, user_id=ctx.user_id)
        return ctx