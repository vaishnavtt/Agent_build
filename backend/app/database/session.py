from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# SQLite requires check_same_thread=False for multi-threaded FastAPI workers
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# echo=False prevents raw SQL queries and bound parameters from leaking into logs
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
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


def init_db(target_engine=None, run_alembic: bool = True) -> None:
    """Initialize database tables using versioned Alembic migrations without data loss."""
    from app.database.base import Base
    import app.models  # Ensure all models are registered

    bind_engine = target_engine or engine

    # For persistent SQLite / Postgres instances, run additive versioned migrations
    if run_alembic and not str(bind_engine.url).startswith("sqlite:///:memory:"):
        from app.database.migration_runner import run_migrations
        try:
            run_migrations(str(bind_engine.url))
            return
        except Exception:
            # Fall back to additive metadata creation if Alembic environment is absent
            pass

    Base.metadata.create_all(bind=bind_engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a SQLAlchemy session per request with safe rollback."""
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
