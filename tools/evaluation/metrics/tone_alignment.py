import re

from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.prompts.builders.judge_tone_prompt_builder import build_tone_judge_prompt

from tools.evaluation.metrics.base import (
    MetricDefinition,
    MetricInput,
    MetricScore,
)

_SCORE_PATTERN = re.compile(r"SCORE:\s*(\d+)", re.IGNORECASE)
_JUSTIFICATION_PATTERN = re.compile(r"JUSTIFICATION:\s*(.+)", re.IGNORECASE | re.DOTALL)


def _parse_judge_response(raw: str) -> tuple[int, str]:
    score_match = _SCORE_PATTERN.search(raw)
    justification_match = _JUSTIFICATION_PATTERN.search(raw)

    score = int(score_match.group(1)) if score_match else 3
    score = max(1, min(5, score))
    justification = (
        justification_match.group(1).strip() if justification_match else raw.strip()
    )
    return score, justification


def _normalize_judge_score(score: int) -> float:
    return round((score - 1) / 4, 4)


class ToneAlignmentMetric:
    def __init__(self, language_model_client: LargeLanguageModelClient) -> None:
        self._language_model_client = language_model_client

    @property
    def name(self) -> str:
        return "tone_alignment"

    @property
    def definition(self) -> MetricDefinition:
        return MetricDefinition(
            name=self.name,
            definition=(
                "Measures how well the generated email matches the requested tone."
            ),
            logic=(
                "An LLM judge rates tone alignment 1-5 using a tone-specific rubric, "
                "then normalizes to 0.0-1.0 via (score - 1) / 4."
            ),
            technique="llm_judge",
        )

    async def score(self, input_data: MetricInput) -> MetricScore:
        prompt = build_tone_judge_prompt(
            tone=input_data.tone,
            generated_email=input_data.generated_email,
        )

        raw = await self._language_model_client.generate_content(prompt)
        judge_score, justification = _parse_judge_response(raw)
        value = _normalize_judge_score(judge_score)

        return MetricScore(
            name=self.name,
            value=value,
            details=f"Judge score {judge_score}/5. {justification}",
        )
