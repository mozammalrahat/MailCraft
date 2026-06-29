"""Evaluation metrics package."""

from app.infrastructure.large_language_model.client import LargeLanguageModelClient

from tools.evaluation.metrics.fact_recall import FactRecallMetric
from tools.evaluation.metrics.professional_quality import ProfessionalQualityMetric
from tools.evaluation.metrics.tone_alignment import ToneAlignmentMetric

Metric = FactRecallMetric | ProfessionalQualityMetric | ToneAlignmentMetric


def get_all_metrics(language_model_client: LargeLanguageModelClient) -> list[Metric]:
    """Return all evaluation metrics."""
    return [
        FactRecallMetric(),
        ToneAlignmentMetric(language_model_client),
        ProfessionalQualityMetric(language_model_client),
    ]
