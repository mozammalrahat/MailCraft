"""Backward-compatible evaluation scenario store shim."""

from tools.evaluation.scenario_store import (
    REQUIRED_SCENARIO_COUNT,
    load_scenarios,
)

__all__ = ["REQUIRED_SCENARIO_COUNT", "load_scenarios"]
