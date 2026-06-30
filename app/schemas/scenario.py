"""Scenario API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType


class ScenarioCreateRequest(BaseModel):
    """Create scenario payload."""

    name: str = Field(min_length=1, max_length=120)
    purpose: ApplicationPurpose
    document_type: DocumentType
    system_prompt: str = Field(min_length=1, max_length=20_000)


class ScenarioUpdateRequest(BaseModel):
    """Update scenario payload."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    system_prompt: str | None = Field(default=None, min_length=1, max_length=20_000)


class ScenarioResponse(BaseModel):
    """Scenario API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    purpose: ApplicationPurpose
    document_type: DocumentType
    system_prompt: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
