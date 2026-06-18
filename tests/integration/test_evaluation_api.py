from unittest.mock import AsyncMock, patch

from app.config import Settings, get_settings
from fastapi.testclient import TestClient


def test_evaluation_latest_not_found(client: TestClient) -> None:
    response = client.get("/api/evaluation/latest")
    assert response.status_code == 404


def test_evaluation_run_requires_api_key(client: TestClient) -> None:
    response = client.post("/api/evaluation/run")
    assert response.status_code == 400
    assert "API key" in response.json()["detail"]


def test_evaluation_run_success(client: TestClient) -> None:
    from datetime import UTC, datetime

    from app.schemas.evaluation import (
        EvaluationMetadata,
        EvaluationReport,
        EvaluationSummary,
        ScenarioScore,
        StrategyResult,
    )
    from app.services.evaluation.metrics.base import MetricDefinition

    mock_report = EvaluationReport(
        metadata=EvaluationMetadata(
            generated_at=datetime.now(UTC),
            metrics=[
                MetricDefinition(
                    name="fact_recall",
                    definition="test",
                    logic="test",
                    technique="automated",
                )
            ],
        ),
        strategies={
            "strategy_a": StrategyResult(
                model="gemini-2.0-flash",
                scenarios=[
                    ScenarioScore(
                        scenario_id="s01",
                        scores={"fact_recall": 0.9},
                        generated_email="email",
                    )
                ],
                averages={"fact_recall": 0.9},
            )
        },
        summary=EvaluationSummary(overall_average=0.9),
    )

    test_settings = Settings(google_api_key="test-key")

    from app.dependencies import get_llm_client
    from app.main import app
    from app.services.llm.client import LlmClient

    mock_client = LlmClient(test_settings)
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_llm_client] = lambda: mock_client

    try:
        with patch(
            "app.routers.api.evaluation.run_full_evaluation",
            new_callable=AsyncMock,
            return_value=mock_report,
        ), patch(
            "app.routers.api.evaluation.write_all_reports",
        ):
            response = client.post("/api/evaluation/run")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["summary"]["overall_average"] == 0.9
