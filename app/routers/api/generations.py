from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies.authentication import CurrentUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.api.dependencies.large_language_model import (
    LargeLanguageModelClientDependency,
    SettingsDependency,
)
from app.application.handlers.application_document_handler import (
    ApplicationDocumentHandler,
)
from app.application.serializers.generated_content_serializer import (
    serialize_generated_content,
)
from app.database.models.generated_content import GeneratedContent
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.export.document_pdf_exporter import (
    build_document_pdf,
    pdf_filename,
)
from app.schemas.generated_content import (
    GeneratedContentListResponse,
    GeneratedContentResponse,
)
from app.services.errors import ServiceValidationError

router = APIRouter(prefix="/generations", tags=["generations"])

_application_document_handler = ApplicationDocumentHandler()


@router.get("", response_model=GeneratedContentListResponse)
def list_generations(
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
    settings: SettingsDependency,
    generation_kind: GenerationKind | None = None,
    purpose: ApplicationPurpose | None = None,
    document_type: DocumentType | None = None,
    scenario_id: int | None = None,
    query_text: str | None = Query(default=None, alias="q"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> GeneratedContentListResponse:
    """List generated content for the authenticated user."""
    query = database_session.query(GeneratedContent).filter(
        GeneratedContent.user_id == current_user.id
    )
    if generation_kind:
        query = query.filter(GeneratedContent.generation_kind == generation_kind.value)
    if purpose:
        query = query.filter(GeneratedContent.purpose == purpose.value)
    if document_type:
        query = query.filter(GeneratedContent.document_type == document_type.value)
    if scenario_id:
        query = query.filter(GeneratedContent.scenario_id == scenario_id)
    if query_text:
        like_pattern = f"%{query_text}%"
        query = query.filter(
            GeneratedContent.position_description.ilike(like_pattern)
            | GeneratedContent.metadata_json.ilike(like_pattern)
            | GeneratedContent.subject.ilike(like_pattern)
            | GeneratedContent.intent.ilike(like_pattern)
        )

    total = query.count()
    records = (
        query.options(joinedload(GeneratedContent.scenario))
        .order_by(GeneratedContent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
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
    record = _get_user_generated_content(
        database_session, current_user.id, generation_id
    )
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
    record = _get_user_generated_content(
        database_session, current_user.id, generation_id
    )
    database_session.delete(record)
    database_session.commit()


@router.get("/{generation_id}/pdf")
def export_generation_pdf(
    generation_id: int,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
) -> StreamingResponse:
    """Export generated content as PDF."""
    record = _get_user_generated_content(
        database_session, current_user.id, generation_id
    )
    pdf_bytes = build_document_pdf(record)
    filename = pdf_filename(record)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("", response_model=GeneratedContentResponse, status_code=201)
async def create_generation(
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
    settings: SettingsDependency,
    language_model_client: LargeLanguageModelClientDependency,
    purpose: Annotated[str, Form(...)],
    document_type: Annotated[str, Form(...)],
    scenario_id: Annotated[int, Form(...)],
    position_description: Annotated[str, Form(...)],
    grounding_links: Annotated[list[str], Form()] = [],
    resume_files: Annotated[list[UploadFile], File()] = [],
) -> GeneratedContentResponse:
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
        )
    except ServiceValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


def _get_user_generated_content(
    database_session: Session, user_id: int, generation_id: int,
) -> GeneratedContent:
    """Load a generated content row owned by the user."""
    record = (
        database_session.query(GeneratedContent)
        .options(joinedload(GeneratedContent.scenario))
        .filter(
            GeneratedContent.id == generation_id,
            GeneratedContent.user_id == user_id,
        )
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return record
