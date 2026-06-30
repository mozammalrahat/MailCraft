"""Handler for application document generation."""

from app.application.pipelines.generation_context import GenerationContext
from app.application.pipelines.pipeline_factory import (
    build_application_document_pipeline,
)
from app.application.serializers.generated_content_serializer import (
    serialize_generated_content,
)
from app.core.configuration import Settings
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.infrastructure.storage.base import FileStorage
from app.schemas.generated_content import GeneratedContentResponse
from sqlalchemy.orm import Session


class ApplicationDocumentHandler:
    """Orchestrate application document generation through the pipeline."""

    def __init__(self) -> None:
        self._pipeline = build_application_document_pipeline()

    async def generate(
        self,
        *,
        user_id: int,
        purpose: ApplicationPurpose,
        document_type: DocumentType,
        scenario_id: int,
        position_description: str,
        resume_file_payloads: list[tuple[str, bytes]],
        grounding_links: list[str],
        database_session: Session,
        settings: Settings,
        language_model_client: LargeLanguageModelClient,
        file_storage: FileStorage | None = None,
    ) -> GeneratedContentResponse:
        """Generate and persist an application document."""
        context = GenerationContext(
            user_id=user_id,
            generation_kind=GenerationKind.APPLICATION_DOCUMENT,
            settings=settings,
            database_session=database_session,
            language_model_client=language_model_client,
            purpose=purpose,
            document_type=document_type,
            scenario_id=scenario_id,
            position_description=position_description,
            resume_file_payloads=resume_file_payloads,
            grounding_links=grounding_links,
            file_storage=file_storage,
        )
        context = await self._pipeline.run(context)
        if context.generated_content is None:
            raise RuntimeError("Generated content was not persisted")
        return serialize_generated_content(
            context.generated_content,
            include_raw_content=settings.debug,
        )
