"""Backward-compatible database module."""

from app.database.base import Base
from app.database.engine_manager import (
    get_database_engine_manager,
    initialize_database,
    reset_database_engine,
)
from app.database.models import GeneratedContent, RefreshToken, Scenario, User
from app.database.session import get_database_session

# Legacy aliases
GeneratedDocument = GeneratedContent
get_session_factory = lambda: get_database_engine_manager().get_session_factory()
init_db = initialize_database
get_db = get_database_session

__all__ = [
    "Base",
    "GeneratedContent",
    "GeneratedDocument",
    "RefreshToken",
    "Scenario",
    "User",
    "get_database_session",
    "get_db",
    "get_session_factory",
    "init_db",
    "initialize_database",
    "reset_database_engine",
]
