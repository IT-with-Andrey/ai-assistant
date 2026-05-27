
from backend.app.database.models import Base

from backend.app.database.connection import engine


def intt_db():
    print("Connecting to the database and creating tables")

    Base.metadata.create_all(bind=engine)
    print('Done! Tables created in the assistant database.')


if __name__ == "__main__":
    intt_db()