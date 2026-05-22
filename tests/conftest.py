
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.database.models import Base


@pytest.fixture(scope='function')
def db_session() -> Session:
    """Creates a new database session for a test."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)  # Create tables
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session  # Provide the session to the test
    session.close()  # Clean up after the test
    Base.metadata.drop_all(engine)  # Drop tables after the test
