"""Backward-compatible database session."""

from app.database.session import get_database_session as get_db

__all__ = ["get_db"]
