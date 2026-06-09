
from sqlalchemy.ext.asyncio import create_async_engine ,  AsyncSession , async_sessionmaker

from backend.app.core.config import settings

DATABASE_URL  = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False, future=True) 

AsyncSessionLocal = async_sessionmaker(engine , class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session 