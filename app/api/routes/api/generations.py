import base64
from typing import Annotated

from app.api.dependencies.authentication import CurrentUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.api.dependencies.large_language_model import (
    LargeLanguageModelClientDependency,
    SettingsDependency,
)
from app.api.dependencies.storage import FileStorageDependency
from app.application.handlers.application_document_handler import (
    ApplicationDocumentHandler,
)
from app.application.serializers.generated_content_serializer import (
    serialize_generated_content,
)
from app.application.services.generated_content_service import (
    GeneratedContentFilters,
    GeneratedContentService,
)
from app.application.services.generation_job_service import (
    GenerationJobService,
    enqueue_generation_job,
)
from app.core.exceptions import ServiceValidationError
from app.core.rate_limits import authenticated_rate_limit_key, limiter
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_job_status import GenerationJobStatus
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.export.document_pdf_exporter import (
    build_document_pdf,
    pdf_filename,
)
from app.schemas.generated_content import (
    GeneratedContentListResponse,
    GeneratedContentResponse,
)
from app.schemas.generation_job import GenerationJobEnqueueResponse
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/generations", tags=["generations"])

_application_document_handler = ApplicationDocumentHandler()


@router.get("", response_model=GeneratedContentListResponse)
def list_generations(
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
    settings: SettingsDependency,
    generation_kind: str | None = None,
    purpose: ApplicationPurpose | None = None,
    document_type: DocumentType | None = None,
    scenario_id: int | None = None,
    query_text: str | None = Query(default=None, alias="q"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> GeneratedContentListResponse:
    """List generated content for the authenticated user."""
    service = GeneratedContentService(database_session)
    records, total = service.list_for_user(
        current_user.id,
        filters=GeneratedContentFilters(
            generation_kind=generation_kind,
            purpose=purpose.value if purpose else None,
            document_type=document_type.value if document_type else None,
            scenario_id=scenario_id,
            query_text=query_text,
        ),
        limit=limit,
        offset=offset,
        include_scenario=True,
    )
    return GeneratedContentListResponse(
        items=[
            serialize_generated_content(
                record,
                include_raw_content=settings.debug,
            )
            for record in records
        ],
        total=total,
    )


@router.get("/{generation_id}", response_model=GeneratedContentResponse)
def get_generation(
    generation_id: int,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
    settings: SettingsDependency,
) -> GeneratedContentResponse:
    """Get a single generated content record."""
    service = GeneratedContentService(database_session)
    record = service.get_owned(current_user.id, generation_id)
    return serialize_generated_content(
        record,
        include_raw_content=settings.debug,
    )


@router.delete("/{generation_id}", status_code=204)
def delete_generation(
    generation_id: int,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
) -> None:
    """Delete a generated content record."""
    service = GeneratedContentService(database_session)
    service.delete_owned(current_user.id, generation_id)


@router.get("/{generation_id}/pdf")
def export_generation_pdf(
    generation_id: int,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
) -> StreamingResponse:
    """Export generated content as PDF."""
    service = GeneratedContentService(database_session)
    record = service.get_owned(current_user.id, generation_id)
    pdf_bytes = build_document_pdf(record)
    filename = pdf_filename(record)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "",
    response_model=GeneratedContentResponse,
    status_code=201,
    responses={202: {"model": GenerationJobEnqueueResponse}},
)
@limiter.limit("10/hour", key_func=authenticated_rate_limit_key)
async def create_generation(
    request: Request,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
    settings: SettingsDependency,
    language_model_client: LargeLanguageModelClientDependency,
    file_storage: FileStorageDependency,
    response: Response,
    purpose: Annotated[str, Form(...)],
    document_type: Annotated[str, Form(...)],
    scenario_id: Annotated[int, Form(...)],
    position_description: Annotated[str, Form(max_length=10_000)],
    grounding_links: Annotated[list[str], Form()] = [],  # noqa: B006
    resume_files: Annotated[list[UploadFile], File()] = [],  # noqa: B006
    async_mode: bool = Query(default=False, alias="async"),
) -> GeneratedContentResponse | GenerationJobEnqueueResponse:
    """Create an application document generation."""
    try:
        purpose_enum = ApplicationPurpose(purpose)
        document_type_enum = DocumentType(document_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid purpose or document type",
        ) from exc

    file_payloads: list[tuple[str, bytes]] = []
    for upload in resume_files:
        if upload.filename:
            content = await upload.read()
            file_payloads.append((upload.filename, content))

    links = [link.strip() for link in grounding_links if link.strip()]

    if async_mode:
        if not settings.generation_async_enabled:
            raise HTTPException(
                status_code=400,
                detail="Async generation is disabled",
            )
        job_service = GenerationJobService(database_session)
        job = job_service.create_job(
            user_id=current_user.id,
            kind=GenerationKind.APPLICATION_DOCUMENT.value,
            payload={
                "purpose": purpose_enum.value,
                "document_type": document_type_enum.value,
                "scenario_id": scenario_id,
                "position_description": position_description.strip(),
                "grounding_links": links,
                "resume_files": [
                    {
                        "filename": filename,
                        "content_base64": base64.b64encode(content).decode("ascii"),
                    }
                    for filename, content in file_payloads
                ],
            },
        )
        await enqueue_generation_job(settings, job.id)
        response.status_code = 202
        return GenerationJobEnqueueResponse(
            job_id=job.id,
            status=GenerationJobStatus.QUEUED,
        )

    try:
        return await _application_document_handler.generate(
            user_id=current_user.id,
            purpose=purpose_enum,
            document_type=document_type_enum,
            scenario_id=scenario_id,
            position_description=position_description.strip(),
            resume_file_payloads=file_payloads,
            grounding_links=links,
            database_session=database_session,
            settings=settings,
            language_model_client=language_model_client,
            file_storage=file_storage,
        )
    except ServiceValidationError:
        raise
