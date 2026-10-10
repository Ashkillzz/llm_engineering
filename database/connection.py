import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///deals.db")

# PostgreSQL connection pooling config or SQLite fallback
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables according to SQLAlchemy metadata."""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Retrieve an active database session."""
    return SessionLocal()


def close_db_session(session) -> None:
    """Close and release the database session back to the pool."""
    if session:
        session.close()
