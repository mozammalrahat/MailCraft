"""Unified generated content ORM model."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.database.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.database.models.scenario import Scenario
    from app.database.models.user import User


class GeneratedContent(Base):
    """Persisted legacy email or application document generation."""

    __tablename__ = "generated_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    generation_kind: Mapped[str] = mapped_column(String(32), index=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    raw_subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    humanization_applied: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    # Legacy email fields
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_facts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Application document fields
    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenarios.id"), index=True, nullable=True
    )
    purpose: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    document_type: Mapped[str | None] = mapped_column(
        String(32), index=True, nullable=True
    )
    position_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    grounding_links_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    cv_filenames_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    cv_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    grounding_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="generated_contents")
    scenario: Mapped[Scenario | None] = relationship(
        back_populates="generated_contents"
    )

    @property
    def key_facts(self) -> list[str]:
        """Return parsed key facts for legacy emails."""
        if not self.key_facts_json:
            return []
        return json.loads(self.key_facts_json)

    @key_facts.setter
    def key_facts(self, value: list[str]) -> None:
        """Store key facts as JSON."""
        self.key_facts_json = json.dumps(value)

    @property
    def grounding_links(self) -> list[str]:
        """Return parsed grounding links."""
        if not self.grounding_links_json:
            return []
        return json.loads(self.grounding_links_json)

    @grounding_links.setter
    def grounding_links(self, value: list[str]) -> None:
        """Store grounding links as JSON."""
        self.grounding_links_json = json.dumps(value)

    @property
    def cv_filenames(self) -> list[str]:
        """Return parsed CV filenames."""
        if not self.cv_filenames_json:
            return []
        return json.loads(self.cv_filenames_json)

    @cv_filenames.setter
    def cv_filenames(self, value: list[str]) -> None:
        """Store CV filenames as JSON."""
        self.cv_filenames_json = json.dumps(value)

    @property
    def document_metadata(self) -> dict:
        """Return parsed application document metadata."""
        if not self.metadata_json:
            return {}
        return json.loads(self.metadata_json)

    @document_metadata.setter
    def document_metadata(self, value: dict) -> None:
        """Store application document metadata as JSON."""
        self.metadata_json = json.dumps(value)
