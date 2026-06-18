from collections.abc import Callable

from app.services.prompts.strategy_a import build_strategy_a_prompt
from app.services.prompts.strategy_b import build_strategy_b_prompt

PromptBuilder = Callable[[str, list[str], str], str]

PROMPT_BUILDERS: dict[str, PromptBuilder] = {
    "strategy_a": build_strategy_a_prompt,
    "strategy_b": build_strategy_b_prompt,
}

__all__ = [
    "PROMPT_BUILDERS",
    "PromptBuilder",
    "build_strategy_a_prompt",
    "build_strategy_b_prompt",
]
