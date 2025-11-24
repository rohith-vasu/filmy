from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlmodel import Session

from app.core.settings import settings


# Update your PostgreSQL connection details
username = settings.db.username
password = settings.DB_PASSWORD
host = settings.db.host
port = settings.db.port
database = settings.db.database

database_url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

engine = create_engine(
    database_url,
    pool_size=50,
    max_overflow=100,
    pool_timeout=60,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----------------------------------------------------------------------------------------------------

def get_postgresql_engine():
    """Create an engine to connect to the PostgreSQL database."""

    return engine

# ----------------------------------------------------------------------------------------------------

def get_global_db_session() -> Session:
    """Create a new SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()  # Commit the session after the block is done
    except Exception:
        session.rollback()  # Rollback on error
        raise
    finally:
        session.close()  # Close the session


@contextmanager
def get_global_db_session_ctx() -> Session:
    return get_global_db_session()
