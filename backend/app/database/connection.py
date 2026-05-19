from sqlalchemy import create_engine
# declarative_base — a function that returns a base class. 
# We will inherit all our models (tables) from it.
# This way SQLAlchemy "sees" our classes as tables.
from sqlalchemy.orm import sessionmaker, declarative_base
# sessionmaker — a factory for creating sessions.
# A session is a temporary workspace where you execute queries and changes in the DB.
# declarative_base – function that returns a base class.
# We will inherit all our models (tables) from this class,
# so that SQLAlchemy sees them as table definitions.
# sessionmaker – factory for creating sessions.
# Then either commit or rollback.

# sqlite:/// means using SQLite, and ./assistant.db – path to the database file
# (relative to where the application is started, usually the project root).
DATABASE_URL = 'sqlite:///./assistant.db'

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False}  # only needed for SQLite because by default SQLite
                                               # forbids using the same connection from different threads (crashes with error)
)

# create the session factory
SessionLocal = sessionmaker(
    autocommit=False,                       # Create the SessionLocal session factory.
    autoflush=False,                        # autocommit=False – transactions won't be auto‑committed after each query,
    bind=engine                             # we manage commits manually.
                                            # autoflush=False – changes won't be automatically flushed to the DB before commit,
                                            # we decide when to "flush" the data.
                                            # bind=engine – bind the factory to our engine.
)

Base = declarative_base()  ## All our future models (classes describing tables) will inherit from it.
                           # This allows SQLAlchemy to collect metadata about the DB structure.

# function for obtaining a session (will be used in the API)
# It will be used in API endpoints (via Depends).
def get_db():
    # Create a new session through the factory
    db = SessionLocal()
    try:
        # yield means the function temporarily gives the session to whoever called it
        yield db
    finally:
        # When the work with the session is finished (exit from a with block or request completion),
        # close the session to release resources
        db.close()

"""
Engine — it’s like opening the assistant.db file and getting ready to work with it.

Session factory (SessionLocal) — it’s a machine that stamps out temporary "workstations" (sessions).
Each user request gets its own workstation so they don’t interfere with each other.

Base class — the blueprint foundation. When you create a class for a table (e.g., User), you inherit from Base,
and SQLAlchemy understands: "Aha, this class is a table – let me create it in the database."

get_db() function — an automatic "polite waiter" for each request.
It hands out a session, waits until the work is done, and then carefully closes it so no open connections are left.
"""