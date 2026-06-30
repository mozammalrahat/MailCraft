"""Build LLM-as-judge prompts for tone alignment evaluation."""

from app.prompts.builders.prompt_renderer import render_prompt
from app.prompts.templates.judge_tone import JUDGE_TONE_TEMPLATE
from app.prompts.templates.parts.judge import TONE_JUDGE_RUBRIC


def build_tone_judge_prompt(tone: str, generated_email: str) -> str:
    """Build a judge prompt for tone alignment scoring."""
    return render_prompt(
        JUDGE_TONE_TEMPLATE,
        tone=tone,
        tone_rubric=TONE_JUDGE_RUBRIC,
        generated_email=generated_email,
    )
