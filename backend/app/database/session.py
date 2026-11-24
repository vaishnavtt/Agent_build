from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.database.base import Base

# SQLite requires check_same_thread=False for multi-threaded FastAPI workers
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_tables_and_columns():
    """Ensure all SQLite tables and columns exist on startup."""
    Base.metadata.create_all(bind=engine)
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                # Check workflows columns
                res = conn.execute(text("PRAGMA table_info(workflows)")).fetchall()
                cols = [r[1] for r in res]
                if cols:
                    if "workflow_name" not in cols:
                        conn.execute(text("ALTER TABLE workflows ADD COLUMN workflow_name VARCHAR(120)"))
                    if "workflow_data" not in cols:
                        conn.execute(text("ALTER TABLE workflows ADD COLUMN workflow_data JSON"))
                    conn.commit()

                # Check workflow_executions columns
                res_exec = conn.execute(text("PRAGMA table_info(workflow_executions)")).fetchall()
                cols_exec = [r[1] for r in res_exec]
                if cols_exec:
                    if "execution_status" not in cols_exec:
                        conn.execute(text("ALTER TABLE workflow_executions ADD COLUMN execution_status VARCHAR(30)"))
                    if "start_time" not in cols_exec:
                        conn.execute(text("ALTER TABLE workflow_executions ADD COLUMN start_time DATETIME"))
                    if "end_time" not in cols_exec:
                        conn.execute(text("ALTER TABLE workflow_executions ADD COLUMN end_time DATETIME"))
                    if "execution_logs" not in cols_exec:
                        conn.execute(text("ALTER TABLE workflow_executions ADD COLUMN execution_logs JSON"))
                    conn.commit()
        except Exception:
            pass


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
