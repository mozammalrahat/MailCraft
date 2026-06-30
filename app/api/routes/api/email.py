

from app.api.dependencies.authentication import CurrentUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.api.dependencies.large_language_model import (
    LargeLanguageModelClientDependency,
    SettingsDependency,
)
from app.application.handlers.email_generation_handler import EmailGenerationHandler
from app.application.services.generation_job_service import (
    GenerationJobService,
    enqueue_generation_job,
)
from app.core.rate_limits import authenticated_rate_limit_key, limiter
from app.domain.enums.generation_job_status import GenerationJobStatus
from app.domain.enums.generation_kind import GenerationKind
from app.schemas.email_generation import EmailGenerationRequest, EmailGenerationResponse
from app.schemas.generation_job import GenerationJobEnqueueResponse
from fastapi import APIRouter, HTTPException, Query, Request, Response

router = APIRouter(prefix="/emails", tags=["emails"])

_email_generation_handler = EmailGenerationHandler()


@router.post(
    "/generate",
    response_model=EmailGenerationResponse,
    responses={202: {"model": GenerationJobEnqueueResponse}},
)
@limiter.limit("20/hour", key_func=authenticated_rate_limit_key)
async def generate_email_endpoint(
    http_request: Request,
    request: EmailGenerationRequest,
    current_user: CurrentUserDependency,
    database_session: DatabaseSessionDependency,
    settings: SettingsDependency,
    language_model_client: LargeLanguageModelClientDependency,
    response: Response,
    async_mode: bool = Query(default=False, alias="async"),
) -> EmailGenerationResponse | GenerationJobEnqueueResponse:
    """Generate a legacy intent-based email and persist it."""
    if async_mode:
        if not settings.generation_async_enabled:
            raise HTTPException(
                status_code=400,
                detail="Async generation is disabled",
            )
        job_service = GenerationJobService(database_session)
        job = job_service.create_job(
            user_id=current_user.id,
            kind=GenerationKind.LEGACY_EMAIL.value,
            payload={
                "intent": request.intent,
                "key_facts": request.key_facts,
                "tone": request.tone.value,
                "strategy": request.strategy.value,
            },
        )
        await enqueue_generation_job(settings, job.id)
        response.status_code = 202
        return GenerationJobEnqueueResponse(
            job_id=job.id,
            status=GenerationJobStatus.QUEUED,
        )

    return await _email_generation_handler.generate_from_api(
        request=request,
        user_id=current_user.id,
        database_session=database_session,
        settings=settings,
        language_model_client=language_model_client,
    )
