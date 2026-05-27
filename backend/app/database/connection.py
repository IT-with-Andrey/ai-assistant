
import os 

from sqlalchemy import create_engine

from sqlalchemy.orm  import sessionmaker

DATABASE_URL = "postgresql://postgres:89614756698q@localhost:5432/assistant"

engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """Автоматический раздатчик сессий для наших будущих API-эндпоинтов. """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()