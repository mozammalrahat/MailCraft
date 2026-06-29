"""Backward-compatible evaluation metrics base shim."""

from tools.evaluation.metrics.base import (
    Metric,
    MetricDefinition,
    MetricInput,
    MetricScore,
)

__all__ = ["Metric", "MetricDefinition", "MetricInput", "MetricScore"]
