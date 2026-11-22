from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# SQLite requires check_same_thread=False for multi-threaded FastAPI workers
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce foreign key constraints for SQLite connections."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine=None) -> None:
    """Initialize database tables without deleting existing records."""
    from app.database.base import Base
    import app.models  # Ensure all models are registered

    bind_engine = target_engine or engine
    Base.metadata.create_all(bind=bind_engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context(session_factory=None) -> Generator[Session, None, None]:
    """Context manager for standalone database session operations."""
    factory = session_factory or SessionLocal
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
