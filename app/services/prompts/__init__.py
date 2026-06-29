"""Backward-compatible prompts shim."""

from app.prompts.builders import (
    PROMPT_BUILDERS,
    build_strategy_a_prompt,
    build_strategy_b_prompt,
)

__all__ = [
    "PROMPT_BUILDERS",
    "build_strategy_a_prompt",
    "build_strategy_b_prompt",
]
