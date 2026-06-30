"""Generated content query and mutation service."""

from dataclasses import dataclass

from app.database.models.generated_content import GeneratedContent
from app.database.models.scenario import Scenario
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload


@dataclass(frozen=True)
class GeneratedContentFilters:
    """Filter parameters for listing generated content."""

    generation_kind: str | None = None
    purpose: str | None = None
    document_type: str | None = None
    scenario_id: int | None = None
    query_text: str | None = None


class GeneratedContentService:
    """Owns generated content queries and mutations."""

    def __init__(self, database_session: Session) -> None:
        self._database_session = database_session

    def _apply_filters(
        self,
        query,
        filters: GeneratedContentFilters,
    ):
        if filters.generation_kind:
            query = query.filter(
                GeneratedContent.generation_kind == filters.generation_kind
            )
        if filters.purpose:
            query = query.filter(GeneratedContent.purpose == filters.purpose)
        if filters.document_type:
            query = query.filter(
                GeneratedContent.document_type == filters.document_type
            )
        if filters.scenario_id:
            query = query.filter(GeneratedContent.scenario_id == filters.scenario_id)
        if filters.query_text:
            like_pattern = f"%{filters.query_text}%"
            query = query.filter(
                GeneratedContent.position_description.ilike(like_pattern)
                | GeneratedContent.metadata_json.ilike(like_pattern)
                | GeneratedContent.subject.ilike(like_pattern)
                | GeneratedContent.intent.ilike(like_pattern)
            )
        return query

    def list_for_user(
        self,
        user_id: int,
        *,
        filters: GeneratedContentFilters | None = None,
        limit: int = 50,
        offset: int = 0,
        include_scenario: bool = False,
    ) -> tuple[list[GeneratedContent], int]:
        """List generated content rows for a user."""
        resolved_filters = filters or GeneratedContentFilters()
        query = self._database_session.query(GeneratedContent).filter(
            GeneratedContent.user_id == user_id
        )
        query = self._apply_filters(query, resolved_filters)
        total = query.count()
        if include_scenario:
            query = query.options(joinedload(GeneratedContent.scenario))
        records = (
            query.order_by(GeneratedContent.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return records, total

    def get_owned(self, user_id: int, generation_id: int) -> GeneratedContent:
        """Load a generated content row owned by the user."""
        record = (
            self._database_session.query(GeneratedContent)
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

    def delete_owned(self, user_id: int, generation_id: int) -> None:
        """Delete a generated content row owned by the user."""
        record = self.get_owned(user_id, generation_id)
        self._database_session.delete(record)
        self._database_session.commit()

    def get_dashboard_stats(self, user_id: int) -> dict[str, int]:
        """Return dashboard aggregate counts for a user."""
        base_query = self._database_session.query(GeneratedContent).filter(
            GeneratedContent.user_id == user_id
        )
        scenarios = (
            self._database_session.query(Scenario)
            .filter(Scenario.user_id == user_id)
            .all()
        )
        return {
            "total": base_query.count(),
            "application_documents": base_query.filter(
                GeneratedContent.generation_kind
                == GenerationKind.APPLICATION_DOCUMENT.value
            ).count(),
            "interview": base_query.filter(
                GeneratedContent.purpose == ApplicationPurpose.INTERVIEW.value
            ).count(),
            "ms": base_query.filter(
                GeneratedContent.purpose == ApplicationPurpose.MS.value
            ).count(),
            "phd": base_query.filter(
                GeneratedContent.purpose == ApplicationPurpose.PHD.value
            ).count(),
            "emails": base_query.filter(
                GeneratedContent.document_type == DocumentType.EMAIL.value
            ).count(),
            "cover_letters": base_query.filter(
                GeneratedContent.document_type == DocumentType.COVER_LETTER.value
            ).count(),
            "scenarios": len(scenarios),
        }
