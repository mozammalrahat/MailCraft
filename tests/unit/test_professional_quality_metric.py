from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.evaluation.metrics.base import MetricInput
from app.services.evaluation.metrics.professional_quality import (
    ProfessionalQualityMetric,
)


@pytest.mark.asyncio
async def test_professional_quality_hybrid_score() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(
        return_value="GRAMMAR: 5\nCLARITY: 4\nOPENING: 4"
    )
    metric = ProfessionalQualityMetric(mock_client)

    email = (
        "Subject: Project Update\n\n"
        "Dear Ms. Lee,\n\n"
        "The project remains on track and within budget."
    )
    result = await metric.score(MetricInput(generated_email=email))

    assert result.name == "professional_quality"
    assert 0.0 < result.value <= 1.0
    assert "Automated=" in result.details
    assert "Judge=" in result.details


@pytest.mark.asyncio
async def test_professional_quality_word_count_penalty() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(
        return_value="GRAMMAR: 3\nCLARITY: 3\nOPENING: 3"
    )
    metric = ProfessionalQualityMetric(mock_client)

    long_body = " ".join(["word"] * 300)
    email = f"Subject: Report\n\nDear team,\n\n{long_body}"

    result = await metric.score(MetricInput(generated_email=email))

    assert result.value < 0.9
    assert "Word count penalty" in result.details
