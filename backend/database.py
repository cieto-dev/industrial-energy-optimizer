from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings


# Database URL from configuration
DATABASE_URL = settings.DATABASE_URL


# SQLite requires this option for FastAPI
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)


# Create database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for database models
Base = declarative_base()


def get_db():
    """
    Provide a database session to FastAPI endpoints.

    The session is automatically closed
    after the request is completed.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()