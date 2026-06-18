import logging
from datetime import UTC, datetime

from app.config import Settings
from app.schemas.email import EmailGenerationRequest, EmailStrategy
from app.schemas.evaluation import (
    EvaluationMetadata,
    EvaluationReport,
    EvaluationSummary,
    Scenario,
    ScenarioScore,
    StrategyResult,
)
from app.services.email.generation import generate_email
from app.services.evaluation.metrics import get_all_metrics
from app.services.evaluation.metrics.base import MetricInput
from app.services.evaluation.scenario_store import load_scenarios
from app.services.llm.client import LlmClient

logger = logging.getLogger(__name__)


def _compute_averages(scenario_scores: list[ScenarioScore]) -> dict[str, float]:
    if not scenario_scores:
        return {}

    metric_names = scenario_scores[0].scores.keys()
    averages: dict[str, float] = {}
    for metric_name in metric_names:
        values = [scenario.scores[metric_name] for scenario in scenario_scores]
        averages[metric_name] = round(sum(values) / len(values), 4)
    return averages


async def run_evaluation(
    strategy_key: str,
    llm_client: LlmClient,
    settings: Settings,
    *,
    scenarios: list[Scenario] | None = None,
) -> StrategyResult:
    strategy_config = settings.strategies.get(strategy_key)
    if strategy_config is None:
        msg = f"Unknown strategy: {strategy_key}"
        raise ValueError(msg)

    loaded_scenarios = scenarios or load_scenarios()
    metrics = get_all_metrics(llm_client)
    scenario_scores: list[ScenarioScore] = []

    for scenario in loaded_scenarios:
        logger.info(
            "evaluating scenario",
            extra={"scenario_id": scenario.id, "strategy": strategy_key},
        )

        generation_request = EmailGenerationRequest(
            intent=scenario.intent,
            key_facts=scenario.key_facts,
            tone=scenario.tone,
            strategy=EmailStrategy(strategy_key),
        )
        generated = await generate_email(generation_request, llm_client, settings)

        metric_input = MetricInput(
            generated_email=generated.email,
            key_facts=scenario.key_facts,
            tone=scenario.tone.value,
            reference_email=scenario.reference_email,
        )

        scores: dict[str, float] = {}
        for metric in metrics:
            result = await metric.score(metric_input)
            scores[result.name] = result.value

        scenario_scores.append(
            ScenarioScore(
                scenario_id=scenario.id,
                scores=scores,
                generated_email=generated.email,
            )
        )

    return StrategyResult(
        model=strategy_config.model,
        scenarios=scenario_scores,
        averages=_compute_averages(scenario_scores),
    )


async def run_full_evaluation(
    llm_client: LlmClient,
    settings: Settings,
    *,
    strategies: list[str] | None = None,
    scenarios: list[Scenario] | None = None,
) -> EvaluationReport:
    strategy_keys = strategies or list(settings.strategies.keys())
    metrics = get_all_metrics(llm_client)

    strategy_results: dict[str, StrategyResult] = {}
    for strategy_key in strategy_keys:
        strategy_results[strategy_key] = await run_evaluation(
            strategy_key,
            llm_client,
            settings,
            scenarios=scenarios,
        )

    all_averages = [
        value
        for result in strategy_results.values()
        for value in result.averages.values()
    ]
    overall_average = (
        round(sum(all_averages) / len(all_averages), 4) if all_averages else 0.0
    )

    return EvaluationReport(
        metadata=EvaluationMetadata(
            generated_at=datetime.now(UTC),
            metrics=[metric.definition for metric in metrics],
        ),
        strategies=strategy_results,
        summary=EvaluationSummary(overall_average=overall_average),
    )
