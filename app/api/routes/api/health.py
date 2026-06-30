"""Health check endpoints."""

from app.api.dependencies.large_language_model import (
    LargeLanguageModelClientDependency,
    SettingsDependency,
)
from app.infrastructure.health.checks import run_readiness_checks
from app.schemas.health import HealthCheckResult
from fastapi import APIRouter, Response

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Liveness probe — process is running."""
    return {"status": "ok"}


@router.get("/health/ready", response_model=HealthCheckResult)
async def readiness_check(
    settings: SettingsDependency,
    language_model_client: LargeLanguageModelClientDependency,
    response: Response,
) -> HealthCheckResult:
    """Readiness probe — database and optional LLM checks."""
    result = await run_readiness_checks(settings, language_model_client)
    if result.status == "fail":
        response.status_code = 503
    return result
