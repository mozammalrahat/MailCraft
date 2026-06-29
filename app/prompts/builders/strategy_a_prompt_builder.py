"""Build Strategy A legacy email prompts."""

from app.prompts.builders.key_facts_formatter import format_key_facts_bulleted
from app.prompts.builders.prompt_renderer import render_prompt
from app.prompts.builders.tone_guidance import get_tone_guidance
from app.prompts.templates.parts.strategy_a import (
    STRATEGY_A_FEW_SHOT_EXAMPLES,
    STRATEGY_A_ROLE,
)
from app.prompts.templates.parts.structure import (
    ANTI_PATTERNS,
    COMPOSITION_CHECKLIST,
    OUTPUT_FORMAT,
    WRITING_FRAMEWORK,
)
from app.prompts.templates.strategy_a import STRATEGY_A_TEMPLATE


def build_strategy_a_prompt(intent: str, key_facts: list[str], tone: str) -> str:
    """Assemble the Strategy A prompt from static templates and inputs."""
    return render_prompt(
        STRATEGY_A_TEMPLATE,
        role=STRATEGY_A_ROLE,
        few_shot_examples=STRATEGY_A_FEW_SHOT_EXAMPLES,
        intent=intent,
        key_facts=format_key_facts_bulleted(key_facts, indent="  "),
        tone=tone,
        tone_guidance=get_tone_guidance(tone),
        writing_framework=WRITING_FRAMEWORK,
        output_format=OUTPUT_FORMAT,
        anti_patterns=ANTI_PATTERNS,
        composition_checklist=COMPOSITION_CHECKLIST,
    )
