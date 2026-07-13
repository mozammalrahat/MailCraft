from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.infrastructure.health.checks import run_readiness_checks
from tests.support.settings_factory import build_test_settings


@pytest.mark.asyncio
async def test_run_readiness_checks_database_ok() -> None:
    settings = build_test_settings(health_check_llm_enabled=False)
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
    settings = build_test_settings()

    with patch(
        "app.infrastructure.health.checks.check_database",
        return_value="fail",
    ):
        result = await run_readiness_checks(settings, MagicMock())

    assert result.status == "fail"
    assert result.checks["database"] == "fail"


@pytest.mark.asyncio
async def test_run_readiness_checks_llm_fail_is_degraded() -> None:
    settings = build_test_settings(health_check_llm_enabled=True)
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(side_effect=RuntimeError("llm down"))

    with patch(
        "app.infrastructure.health.checks.check_database",
        return_value="ok",
    ):
        result = await run_readiness_checks(settings, mock_client)

    assert result.status == "degraded"
    assert result.checks["llm"] == "fail"
