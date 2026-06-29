from unittest.mock import AsyncMock, MagicMock

import pytest
from tools.evaluation.metrics.base import MetricInput
from tools.evaluation.metrics.tone_alignment import ToneAlignmentMetric


@pytest.mark.asyncio
async def test_tone_alignment_parses_judge_response() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(
        return_value="SCORE: 4\nJUSTIFICATION: Formal tone maintained throughout."
    )
    metric = ToneAlignmentMetric(mock_client)

    result = await metric.score(
        MetricInput(
            generated_email="Dear team,\n\nPlease review the attached proposal.",
            tone="formal",
        )
    )

    assert result.name == "tone_alignment"
    assert result.value == 0.75
    assert "4/5" in result.details


@pytest.mark.asyncio
async def test_tone_alignment_defaults_when_unparseable() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(return_value="Looks good overall.")
    metric = ToneAlignmentMetric(mock_client)

    result = await metric.score(
        MetricInput(generated_email="Hi team,\n\nQuick update.", tone="casual")
    )

    assert result.value == 0.5
