"""Application document generation schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums.application_purpose import ApplicationPurpose


class ApplicationDocumentMetadata(BaseModel):
    """Structured metadata from application document generation."""

    model_config = ConfigDict(extra="forbid")

    generation_reason: str = ""
    organization: str = ""
    position_title: str = ""
    recipient_name: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    key_highlights_used: list[str] = Field(default_factory=list)
    tone_used: str = "formal"


class StructuredApplicationDocumentOutput(BaseModel):
    """Structured LLM output for application documents."""

    model_config = ConfigDict(extra="forbid")

    subject: str = ""
    body: str
    metadata: ApplicationDocumentMetadata


# Backward-compatible aliases
Purpose = ApplicationPurpose
GenerationMetadata = ApplicationDocumentMetadata
StructuredGenerationOutput = StructuredApplicationDocumentOutput
