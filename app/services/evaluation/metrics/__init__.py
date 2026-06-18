from app.services.evaluation.metrics.base import Metric
from app.services.evaluation.metrics.fact_recall import FactRecallMetric
from app.services.evaluation.metrics.professional_quality import (
    ProfessionalQualityMetric,
)
from app.services.evaluation.metrics.tone_alignment import ToneAlignmentMetric
from app.services.llm.client import LlmClient


def get_all_metrics(llm_client: LlmClient) -> list[Metric]:
    return [
        FactRecallMetric(),
        ToneAlignmentMetric(llm_client),
        ProfessionalQualityMetric(llm_client),
    ]
