import asyncio
from .base import BaseMiddleware, ChatContext
from backend.app.database.repository import MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession

class LoadHistoryMiddleware(BaseMiddleware):
    def __init__(self, db: AsyncSession):
        self.repo = MessageRepository(db)
    async def process(self, ctx: ChatContext) -> ChatContext:
        messages = await self.repo.get_last(limit=10, user_id=ctx.user_id)
        ctx.history = [{"role": m.role.value, "content": m.content} for m in messages]
        return ctx