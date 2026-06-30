"""Build LLM-as-judge prompts for professional quality evaluation."""

from app.prompts.builders.prompt_renderer import render_prompt
from app.prompts.templates.judge_quality import JUDGE_QUALITY_TEMPLATE
from app.prompts.templates.parts.judge import QUALITY_JUDGE_RUBRIC


def build_quality_judge_prompt(generated_email: str) -> str:
    """Build a judge prompt for grammar, clarity, and opening quality."""
    return render_prompt(
        JUDGE_QUALITY_TEMPLATE,
        quality_rubric=QUALITY_JUDGE_RUBRIC,
        generated_email=generated_email,
    )
