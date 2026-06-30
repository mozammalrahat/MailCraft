"""Shared context passed through generation pipeline steps."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.core.configuration import Settings
from app.database.models.generated_content import GeneratedContent
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.infrastructure.storage.base import FileStorage


@dataclass
class GenerationContext:
    """Mutable context for a single generation run."""

    user_id: int
    generation_kind: GenerationKind
    settings: Settings
    database_session: Session
    language_model_client: LargeLanguageModelClient

    purpose: ApplicationPurpose | None = None
    document_type: DocumentType | None = None
    scenario_id: int | None = None
    position_description: str | None = None
    resume_file_payloads: list[tuple[str, bytes]] = field(default_factory=list)
    grounding_links: list[str] = field(default_factory=list)
    file_storage: "FileStorage | None" = None
    resume_storage_keys: list[dict[str, str]] = field(default_factory=list)

    resume_text: str = ""
    resume_filenames: list[str] = field(default_factory=list)
    system_instruction: str = ""
    user_prompt: str = ""
    structured_output: dict = field(default_factory=dict)
    grounding_metadata: dict | None = None

    subject: str | None = None
    body: str = ""
    raw_subject: str | None = None
    raw_body: str | None = None
    clipboard_text: str = ""
    model_name: str | None = None
    humanization_applied: bool = False
    humanizer_model_name: str | None = None
    humanizer_prompt_version: str | None = None
    document_metadata: dict = field(default_factory=dict)
    generated_content: GeneratedContent | None = None

    validation_errors: list[str] = field(default_factory=list)
