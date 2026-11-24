import pytest
from app.database.session import SessionLocal, ensure_tables_and_columns


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure all tables and columns exist before running test suite."""
    ensure_tables_and_columns()
    yield


@pytest.fixture
def db_session():
    """Provides a transactional database session for a test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
