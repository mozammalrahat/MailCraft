"""Infrastructure health check helpers."""

import asyncio
import logging

from app.core.configuration import Settings
from app.database.engine_manager import get_database_engine_manager
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.schemas.health import CheckStatus, HealthCheckResult, HealthStatus
from sqlalchemy import text

logger = logging.getLogger(__name__)


def check_database() -> CheckStatus:
    """Verify database connectivity with SELECT 1."""
    try:
        engine = get_database_engine_manager().get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        logger.exception("Database health check failed")
        return "fail"


async def check_llm(
    settings: Settings,
    language_model_client: LargeLanguageModelClient,
) -> CheckStatus:
    """Optionally ping the configured LLM provider."""
    if not settings.health_check_llm_enabled:
        return "skipped"

    try:
        await asyncio.wait_for(
            language_model_client.generate_content(
                "ping",
                model=settings.google_judge_model,
            ),
            timeout=settings.health_check_llm_timeout_seconds,
        )
        return "ok"
    except Exception:
        logger.warning("LLM health check failed", exc_info=True)
        return "fail"


async def run_readiness_checks(
    settings: Settings,
    language_model_client: LargeLanguageModelClient | None = None,
) -> HealthCheckResult:
    """Run readiness checks for database and optional LLM."""
    checks: dict[str, CheckStatus] = {
        "database": check_database(),
    }

    if language_model_client is not None:
        checks["llm"] = await check_llm(settings, language_model_client)
    else:
        checks["llm"] = "skipped" if not settings.health_check_llm_enabled else "fail"

    if checks["database"] == "fail":
        status: HealthStatus = "fail"
    elif checks.get("llm") == "fail":
        status = "degraded"
    else:
        status = "ok"

    return HealthCheckResult(status=status, checks=checks)
