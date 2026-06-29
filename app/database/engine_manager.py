"""Singleton database engine and session factory lifecycle."""

from pathlib import Path

from app.core.configuration import get_settings
from app.database.base import Base
from app.database.migrations import run_database_migrations
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


class DatabaseEngineManager:
    """Manages SQLAlchemy engine and session factory lifecycle."""

    _instance: "DatabaseEngineManager | None" = None

    def __init__(self) -> None:
        self._engine: Engine | None = None
        self._session_factory: sessionmaker | None = None

    @classmethod
    def get_instance(cls) -> "DatabaseEngineManager":
        """Return the singleton engine manager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, database_url: str | None = None, upload_dir: str | None = None) -> None:
        """Create engine, session factory, and required directories."""
        settings = get_settings()
        resolved_url = database_url or settings.database_url
        resolved_upload_dir = upload_dir or settings.upload_dir

        if resolved_url.startswith("sqlite:///./"):
            database_path = resolved_url.replace("sqlite:///./", "")
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(resolved_upload_dir).mkdir(parents=True, exist_ok=True)

        connect_args = (
            {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
        )
        self._engine = create_engine(resolved_url, connect_args=connect_args)
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
        )

    def dispose(self) -> None:
        """Dispose engine and clear session factory."""
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None

    def create_all_tables(self) -> None:
        """Create all tables registered on the declarative base."""
        if self._engine is None:
            raise RuntimeError("Database engine is not initialized")
        Base.metadata.create_all(bind=self._engine)

    def get_session_factory(self) -> sessionmaker:
        """Return the configured session factory."""
        if self._session_factory is None:
            self.initialize()
        assert self._session_factory is not None
        return self._session_factory

    def get_engine(self) -> Engine:
        """Return the configured SQLAlchemy engine."""
        if self._engine is None:
            self.initialize()
        assert self._engine is not None
        return self._engine


def get_database_engine_manager() -> DatabaseEngineManager:
    """Return the shared database engine manager."""
    return DatabaseEngineManager.get_instance()


def initialize_database() -> None:
    """Initialize database engine and apply Alembic migrations."""
    manager = get_database_engine_manager()
    manager.initialize()
    run_database_migrations()


def reset_database_engine() -> None:
    """Reset engine manager for tests or configuration changes."""
    get_database_engine_manager().dispose()
