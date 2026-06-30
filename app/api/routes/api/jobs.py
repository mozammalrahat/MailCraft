"""Async generation job routes."""

from app.api.dependencies.authentication import CurrentUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.application.services.generation_job_service import GenerationJobService
from app.schemas.generation_job import GenerationJobResponse
from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=GenerationJobResponse)
def get_generation_job(
    job_id: str,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
) -> GenerationJobResponse:
    """Poll async generation job status."""
    service = GenerationJobService(database_session)
    job = service.get_owned(current_user.id, job_id)
    return GenerationJobResponse.model_validate(job)
