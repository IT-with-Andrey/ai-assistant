
import enum

from datetime import datetime

from sqlalchemy import Text , DateTime , Enum , func , Index

from sqlalchemy.orm import DeclarativeBase , Mapped  , mapped_column



class Base(DeclarativeBase):
    pass


class MessageRole(str, enum.Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole , name='message_role_enum' , create_type=True),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text , nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        Index('ix_messages_created_at' ,"created_at" ),
    ) 