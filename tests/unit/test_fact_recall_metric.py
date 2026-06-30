import pytest
from tools.evaluation.metrics.base import MetricInput
from tools.evaluation.metrics.fact_recall import FactRecallMetric


@pytest.fixture
def metric() -> FactRecallMetric:
    return FactRecallMetric()


@pytest.mark.asyncio
async def test_fact_recall_all_facts_present(metric: FactRecallMetric) -> None:
    result = await metric.score(
        MetricInput(
            generated_email=(
                "Subject: Follow-Up\n\n"
                "Demo held on May 12. Prospect requested pricing for 50 seats."
            ),
            key_facts=[
                "Demo held on May 12",
                "Prospect requested pricing for 50 seats",
            ],
        )
    )

    assert result.name == "fact_recall"
    assert result.value == 1.0


@pytest.mark.asyncio
async def test_fact_recall_partial_match(metric: FactRecallMetric) -> None:
    result = await metric.score(
        MetricInput(
            generated_email="Subject: Update\n\nDemo held on May 12 only.",
            key_facts=[
                "Demo held on May 12",
                "Prospect requested pricing for 50 seats",
            ],
        )
    )

    assert 0.0 < result.value < 1.0
    assert "Missed" in result.details


@pytest.mark.asyncio
async def test_fact_recall_no_facts(metric: FactRecallMetric) -> None:
    result = await metric.score(
        MetricInput(generated_email="Subject: Test\n\nBody", key_facts=[])
    )
    assert result.value == 1.0


@pytest.mark.asyncio
async def test_fact_recall_fact_in_subject_only(metric: FactRecallMetric) -> None:
    result = await metric.score(
        MetricInput(
            generated_email="Subject: Demo on May 12\n\nDear team,\n\nQuick update.",
            key_facts=["Demo on May 12"],
        )
    )

    assert result.value == 1.0
