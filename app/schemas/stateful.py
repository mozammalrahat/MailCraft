"""Backward-compatible schema re-exports."""

from app.domain.enums.application_purpose import ApplicationPurpose as Purpose
from app.domain.enums.document_type import DocumentType
from app.schemas.application_document import (
    ApplicationDocumentMetadata as GenerationMetadata,
)
from app.schemas.application_document import (
    StructuredApplicationDocumentOutput as StructuredGenerationOutput,
)
from app.schemas.authentication import UserLoginRequest as UserLogin
from app.schemas.authentication import UserRegistrationRequest as UserRegister
from app.schemas.generated_content import (
    GeneratedContentListResponse as GenerationListResponse,
)
from app.schemas.generated_content import (
    GeneratedContentResponse as GeneratedDocumentOut,
)
from app.schemas.scenario import ScenarioCreateRequest as ScenarioCreate
from app.schemas.scenario import ScenarioResponse as ScenarioOut
from app.schemas.scenario import ScenarioUpdateRequest as ScenarioUpdate

__all__ = [
    "DocumentType",
    "GeneratedDocumentOut",
    "GenerationListResponse",
    "GenerationMetadata",
    "Purpose",
    "ScenarioCreate",
    "ScenarioOut",
    "ScenarioUpdate",
    "StructuredGenerationOutput",
    "UserLogin",
    "UserRegister",
]
