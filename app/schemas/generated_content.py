"""Unified generated content API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind


class GeneratedContentResponse(BaseModel):
    """Serialized generated content for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    generation_kind: GenerationKind
    purpose: ApplicationPurpose | None = None
    document_type: DocumentType | None = None
    scenario_id: int | None = None
    scenario_name: str = ""
    position_description: str | None = None
    grounding_links: list[str] = []
    cv_filenames: list[str] = []
    intent: str | None = None
    key_facts: list[str] = []
    tone: str | None = None
    strategy: str | None = None
    subject: str | None
    body: str
    raw_subject: str | None = None
    raw_body: str | None = None
    humanization_applied: bool = False
    clipboard_text: str = ""
    metadata_json: dict = {}
    created_at: datetime


class GeneratedContentListResponse(BaseModel):
    """Paginated generated content list."""

    items: list[GeneratedContentResponse]
    total: int
