import os
from typing import Optional
from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.core.logging import logger


def get_alembic_config(target_url: Optional[str] = None) -> Config:
    """Resolve and configure Alembic Config object."""
    # Look for alembic.ini in backend/ or root
    backend_ini = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
    )
    root_ini = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "alembic.ini")
    )

    ini_path = backend_ini if os.path.exists(backend_ini) else root_ini
    cfg = Config(ini_path)

    url = target_url or settings.DATABASE_URL
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def run_migrations(target_url: Optional[str] = None) -> None:
    """Execute all pending Alembic migrations up to head in a versioned, additive manner."""
    try:
        cfg = get_alembic_config(target_url)
        logger.info("Running database migrations to head...")
        command.upgrade(cfg, "head")
        logger.info("Database migrations completed successfully.")
    except Exception as exc:
        logger.error("Failed executing database migrations: %s", exc)
        raise
