from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.models import Message


class MessageRepository:
    """
    Handles persistence of chat messages.

    Instantiate with a SQLAlchemy Session and call methods to save or retrieve
    messages. ``user_id`` parameter is accepted and passed to the model.
    """

    def __init__(self, db: AsyncSession):
        self.db = db


    async def save(self, role: str, content: str, user_id: str = "default_user") -> Message:
        """
        Persist a new message.

        Args:
            role: Message role ('user', 'assistant', 'system').
            content: Text content of the message.
            user_id: Identifier of the user.

        Returns:
            The persisted Message instance.
        """
        msg = Message(role=role, content=content, user_id=user_id)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_last(self, limit: int = 10, user_id: str = "default_user"):
        """
        Retrieve the most recent messages for a user, ordered by creation time
        (oldest first for conversation continuity).
        """
        stmt = (
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        return list(messages)[::-1]   # reverse to chronological order