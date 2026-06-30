from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.configuration import Settings
from app.schemas.evaluation import EvaluationReport, Scenario
from tools.evaluation.metrics.base import MetricDefinition, MetricScore
from tools.evaluation.metrics.fact_recall import FactRecallMetric
from tools.evaluation.report_writer import write_all_reports
from tools.evaluation.runner import run_evaluation, run_full_evaluation


def _mock_llm_metric(name: str, value: float) -> MagicMock:
    metric = MagicMock()
    metric.name = name
    metric.definition = MetricDefinition(
        name=name,
        definition="mock",
        logic="mock",
        technique="llm_judge",
    )
    metric.score = AsyncMock(
        return_value=MetricScore(name=name, value=value, details="ok")
    )
    return metric


def _sample_scenarios() -> list[Scenario]:
    return [
        Scenario(
            id="s01",
            intent="Follow up",
            key_facts=["Demo on May 12"],
            tone="formal",
            reference_email="Subject: Follow up\n\nDemo on May 12.",
        ),
        Scenario(
            id="s02",
            intent="Sprint update",
            key_facts=["Sprint ends Friday"],
            tone="casual",
            reference_email="Subject: Update\n\nSprint ends Friday.",
        ),
    ]


@pytest.mark.asyncio
async def test_run_evaluation_scores_all_scenarios() -> None:
    settings = Settings(google_api_key="test-key")
    mock_client = MagicMock()

    from app.schemas.email_generation import EmailGenerationResponse

    generated_responses = [
        EmailGenerationResponse(
            email="Demo on May 12.",
            subject="Follow up",
            model="gemini-2.5-flash",
            strategy="strategy_a",
            prompt_version="2.0.0",
        ),
        EmailGenerationResponse(
            email="Sprint ends Friday.",
            subject="Sprint update",
            model="gemini-2.5-flash",
            strategy="strategy_a",
            prompt_version="2.0.0",
        ),
    ]

    mock_metrics = [
        FactRecallMetric(),
        _mock_llm_metric("tone_alignment", 0.8),
        _mock_llm_metric("professional_quality", 0.85),
    ]
    captured_inputs: list = []

    async def capture_score(input_data):
        captured_inputs.append(input_data)
        return MetricScore(name="fact_recall", value=1.0, details="ok")

    mock_metrics[0].score = capture_score

    with (
        patch(
            "tools.evaluation.runner.generate_email",
            new_callable=AsyncMock,
            side_effect=generated_responses,
        ),
        patch(
            "tools.evaluation.runner.get_all_metrics",
            return_value=mock_metrics,
        ),
    ):
        result = await run_evaluation(
            "strategy_a",
            mock_client,
            settings,
            scenarios=_sample_scenarios(),
        )

    assert len(result.scenarios) == 2
    assert "fact_recall" in result.averages
    assert captured_inputs[0].generated_email.startswith("Subject: Follow up")
    assert result.scenarios[0].generated_email.startswith("Subject: Follow up")


@pytest.mark.asyncio
async def test_run_full_evaluation_builds_report() -> None:
    settings = Settings(google_api_key="test-key")
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(
        return_value="Subject: Test\n\nDear team,\n\nDemo on May 12."
    )

    with patch(
        "tools.evaluation.runner.run_evaluation",
        new_callable=AsyncMock,
    ) as mock_run:
        from app.schemas.evaluation import ScenarioScore, StrategyResult

        mock_run.side_effect = [
            StrategyResult(
                model="gemini-2.5-flash",
                scenarios=[
                    ScenarioScore(
                        scenario_id="s01",
                        scores={
                            "fact_recall": 1.0,
                            "tone_alignment": 0.8,
                            "professional_quality": 0.85,
                        },
                        generated_email="email-a",
                    )
                ],
                averages={
                    "fact_recall": 1.0,
                    "tone_alignment": 0.8,
                    "professional_quality": 0.85,
                },
            ),
            StrategyResult(
                model="gemini-2.5-flash",
                scenarios=[
                    ScenarioScore(
                        scenario_id="s01",
                        scores={
                            "fact_recall": 0.5,
                            "tone_alignment": 0.6,
                            "professional_quality": 0.7,
                        },
                        generated_email="email-b",
                    )
                ],
                averages={
                    "fact_recall": 0.5,
                    "tone_alignment": 0.6,
                    "professional_quality": 0.7,
                },
            ),
        ]

        report = await run_full_evaluation(
            mock_client,
            settings,
            strategies=["strategy_a", "strategy_b"],
            scenarios=_sample_scenarios()[:1],
        )

    assert len(report.strategies) == 2
    assert len(report.metadata.metrics) == 3
    assert report.summary.overall_average > 0


def test_write_all_reports(tmp_path) -> None:
    from app.schemas.evaluation import (
        EvaluationMetadata,
        EvaluationSummary,
        ScenarioScore,
        StrategyResult,
    )
    from tools.evaluation.metrics.base import MetricDefinition

    report = EvaluationReport(
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
                model="gemini-2.5-flash",
                scenarios=[
                    ScenarioScore(
                        scenario_id="s01",
                        scores={"fact_recall": 0.9},
                        generated_email="test email",
                    )
                ],
                averages={"fact_recall": 0.9},
            )
        },
        summary=EvaluationSummary(overall_average=0.9),
    )

    written = write_all_reports(report, output_dir=tmp_path)
    assert written["evaluation_summary.csv"].exists()
    assert written["evaluation_comparison.json"].exists()
