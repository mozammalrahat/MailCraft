"""API dependencies for database sessions."""

from typing import Annotated

from app.database.session import get_database_session
from fastapi import Depends
from sqlalchemy.orm import Session

DatabaseSessionDependency = Annotated[Session, Depends(get_database_session)]
