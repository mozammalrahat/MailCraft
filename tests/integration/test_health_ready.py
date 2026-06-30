from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_readiness_check_ok(client: TestClient) -> None:
    with patch(
        "app.api.routes.api.health.run_readiness_checks",
        new_callable=AsyncMock,
    ) as mock_checks:
        from app.schemas.health import HealthCheckResult

        mock_checks.return_value = HealthCheckResult(
            status="ok",
            checks={"database": "ok", "llm": "skipped"},
        )
        response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_check_fail_returns_503(client: TestClient) -> None:
    with patch(
        "app.api.routes.api.health.run_readiness_checks",
        new_callable=AsyncMock,
    ) as mock_checks:
        from app.schemas.health import HealthCheckResult

        mock_checks.return_value = HealthCheckResult(
            status="fail",
            checks={"database": "fail", "llm": "skipped"},
        )
        response = client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "fail"
