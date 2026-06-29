"""Shared context passed through generation pipeline steps."""

from dataclasses import dataclass, field

from app.core.configuration import Settings
from app.database.models.generated_content import GeneratedContent
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.email_strategy import EmailStrategy
from app.domain.enums.email_tone import EmailTone
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from sqlalchemy.orm import Session


@dataclass
class GenerationContext:
    """Mutable context for a single generation run."""

    user_id: int
    generation_kind: GenerationKind
    settings: Settings
    database_session: Session
    language_model_client: LargeLanguageModelClient

    # Legacy email inputs
    intent: str | None = None
    key_facts: list[str] = field(default_factory=list)
    tone: EmailTone | None = None
    strategy: EmailStrategy | None = None

    # Application document inputs
    purpose: ApplicationPurpose | None = None
    document_type: DocumentType | None = None
    scenario_id: int | None = None
    position_description: str | None = None
    resume_file_payloads: list[tuple[str, bytes]] = field(default_factory=list)
    grounding_links: list[str] = field(default_factory=list)

    # Intermediate outputs
    resume_text: str = ""
    resume_filenames: list[str] = field(default_factory=list)
    system_instruction: str = ""
    user_prompt: str = ""
    raw_language_model_output: str = ""
    structured_output: dict = field(default_factory=dict)
    grounding_metadata: dict | None = None

    # Final outputs
    subject: str | None = None
    body: str = ""
    raw_subject: str | None = None
    raw_body: str | None = None
    clipboard_text: str = ""
    model_name: str | None = None
    prompt_version: str | None = None
    humanization_applied: bool = False
    humanizer_model_name: str | None = None
    humanizer_prompt_version: str | None = None
    document_metadata: dict = field(default_factory=dict)
    generated_content: GeneratedContent | None = None

    # Validation errors collected by steps
    validation_errors: list[str] = field(default_factory=list)
