"""Prompt builder exports."""

from app.prompts.builders.strategy_a_prompt_builder import build_strategy_a_prompt
from app.prompts.builders.strategy_b_prompt_builder import build_strategy_b_prompt

PROMPT_BUILDERS = {
    "strategy_a": build_strategy_a_prompt,
    "strategy_b": build_strategy_b_prompt,
}

__all__ = [
    "PROMPT_BUILDERS",
    "build_strategy_a_prompt",
    "build_strategy_b_prompt",
]
