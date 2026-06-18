from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import get_llm_client
from app.schemas.email import EmailGenerationRequest, EmailGenerationResponse
from app.services.email.generation import generate_email
from app.services.llm.client import LlmClient

router = APIRouter(prefix="/emails", tags=["emails"])

LlmClientDep = Annotated[LlmClient, Depends(get_llm_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/generate", response_model=EmailGenerationResponse)
async def generate_email_endpoint(
    request: EmailGenerationRequest,
    llm_client: LlmClientDep,
    settings: SettingsDep,
) -> EmailGenerationResponse:
    return await generate_email(request, llm_client, settings)
