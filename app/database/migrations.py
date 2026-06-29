"""Run Alembic migrations against the configured database."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def run_database_migrations() -> None:
    """Apply all pending Alembic migrations."""
    project_root = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(project_root / "alembic.ini"))
    command.upgrade(alembic_config, "head")
