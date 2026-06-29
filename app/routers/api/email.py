
from fastapi import APIRouter

from app.api.dependencies.authentication import CurrentUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.api.dependencies.large_language_model import (
    LargeLanguageModelClientDependency,
    SettingsDependency,
)
from app.application.handlers.email_generation_handler import EmailGenerationHandler
from app.schemas.email_generation import EmailGenerationRequest, EmailGenerationResponse

router = APIRouter(prefix="/emails", tags=["emails"])

_email_generation_handler = EmailGenerationHandler()


@router.post("/generate", response_model=EmailGenerationResponse)
async def generate_email_endpoint(
    request: EmailGenerationRequest,
    current_user: CurrentUserDependency,
    database_session: DatabaseSessionDependency,
    settings: SettingsDependency,
    language_model_client: LargeLanguageModelClientDependency,
) -> EmailGenerationResponse:
    """Generate a legacy intent-based email and persist it."""
    return await _email_generation_handler.generate_from_api(
        request=request,
        user_id=current_user.id,
        database_session=database_session,
        settings=settings,
        language_model_client=language_model_client,
    )
