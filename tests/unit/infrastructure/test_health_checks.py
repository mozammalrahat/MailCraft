from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.configuration import Settings
from app.infrastructure.health.checks import run_readiness_checks


@pytest.mark.asyncio
async def test_run_readiness_checks_database_ok() -> None:
    settings = Settings(
        GOOGLE_MODEL_A="gemini-test",
        GOOGLE_MODEL_B="gemini-test",
        GOOGLE_JUDGE_MODEL="gemini-test",
        health_check_llm_enabled=False,
    )
    mock_client = MagicMock()

    with patch(
        "app.infrastructure.health.checks.check_database",
        return_value="ok",
    ):
        result = await run_readiness_checks(settings, mock_client)

    assert result.status == "ok"
    assert result.checks["database"] == "ok"
    assert result.checks["llm"] == "skipped"


@pytest.mark.asyncio
async def test_run_readiness_checks_database_fail() -> None:
    settings = Settings(
        GOOGLE_MODEL_A="gemini-test",
        GOOGLE_MODEL_B="gemini-test",
        GOOGLE_JUDGE_MODEL="gemini-test",
    )

    with patch(
        "app.infrastructure.health.checks.check_database",
        return_value="fail",
    ):
        result = await run_readiness_checks(settings, MagicMock())

    assert result.status == "fail"
    assert result.checks["database"] == "fail"


@pytest.mark.asyncio
async def test_run_readiness_checks_llm_fail_is_degraded() -> None:
    settings = Settings(
        GOOGLE_MODEL_A="gemini-test",
        GOOGLE_MODEL_B="gemini-test",
        GOOGLE_JUDGE_MODEL="gemini-test",
        health_check_llm_enabled=True,
    )
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(side_effect=RuntimeError("llm down"))

    with patch(
        "app.infrastructure.health.checks.check_database",
        return_value="ok",
    ):
        result = await run_readiness_checks(settings, mock_client)

    assert result.status == "degraded"
    assert result.checks["llm"] == "fail"
