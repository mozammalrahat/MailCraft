"""Database session dependency for FastAPI."""

from collections.abc import Generator

from app.database.engine_manager import get_database_engine_manager
from sqlalchemy.orm import Session


def get_database_session() -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session."""
    session_factory = get_database_engine_manager().get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
