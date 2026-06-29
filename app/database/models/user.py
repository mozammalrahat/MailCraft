"""User ORM model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.database.base import Base
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.database.models.generated_content import GeneratedContent
    from app.database.models.refresh_token import RefreshToken
    from app.database.models.scenario import Scenario


class User(Base):
    """Authenticated MailCraft user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user")
    scenarios: Mapped[list[Scenario]] = relationship(back_populates="user")
    generated_contents: Mapped[list[GeneratedContent]] = relationship(
        back_populates="user"
    )
