import re

from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.prompts.builders.judge_quality_prompt_builder import build_quality_judge_prompt

from tools.evaluation.metrics.base import (
    MetricDefinition,
    MetricInput,
    MetricScore,
)

_SUBJECT_PATTERN = re.compile(r"^Subject:\s*.+$", re.MULTILINE | re.IGNORECASE)
_GREETING_PATTERN = re.compile(
    r"\b(dear|hi|hello|good morning|good afternoon)\b", re.IGNORECASE
)
_JUDGE_SCORE_PATTERN = re.compile(
    r"GRAMMAR:\s*(\d+).*CLARITY:\s*(\d+).*OPENING:\s*(\d+)",
    re.IGNORECASE | re.DOTALL,
)


def _automated_score(email: str) -> tuple[float, str]:
    words = email.split()
    word_count = len(words)
    details: list[str] = []

    word_score = 1.0
    if word_count > 250:
        word_score = max(0.0, 1.0 - (word_count - 250) / 250)
        details.append(f"Word count penalty ({word_count} words).")
    else:
        details.append(f"Word count OK ({word_count} words).")

    subject_score = 1.0 if _SUBJECT_PATTERN.search(email) else 0.0
    if subject_score:
        details.append("Subject line detected.")
    else:
        details.append("Subject line missing.")

    greeting_score = 1.0 if _GREETING_PATTERN.search(email) else 0.0
    if greeting_score:
        details.append("Greeting detected.")
    else:
        details.append("Greeting missing.")

    automated = (word_score + subject_score + greeting_score) / 3
    return round(automated, 4), "; ".join(details)


def _parse_quality_judge(raw: str) -> tuple[float, str]:
    match = _JUDGE_SCORE_PATTERN.search(raw)
    if not match:
        return 0.6, raw.strip()

    grammar = max(1, min(5, int(match.group(1))))
    clarity = max(1, min(5, int(match.group(2))))
    opening = max(1, min(5, int(match.group(3))))
    avg = (grammar + clarity + opening) / 3
    normalized = round((avg - 1) / 4, 4)
    return normalized, (
        f"Grammar {grammar}/5, Clarity {clarity}/5, Opening {opening}/5."
    )


class ProfessionalQualityMetric:
    def __init__(self, language_model_client: LargeLanguageModelClient) -> None:
        self._language_model_client = language_model_client

    @property
    def name(self) -> str:
        return "professional_quality"

    @property
    def definition(self) -> MetricDefinition:
        return MetricDefinition(
            name=self.name,
            definition=(
                "Measures professional quality via conciseness, structure, "
                "and writing clarity."
            ),
            logic=(
                "40% automated: word-count penalty above 250 words, "
                "subject-line presence, greeting detection. "
                "60% LLM judge: grammar, clarity, and opening effectiveness "
                "rated 1-5 and normalized."
            ),
            technique="hybrid",
        )

    async def score(self, input_data: MetricInput) -> MetricScore:
        automated, automated_details = _automated_score(input_data.generated_email)

        judge_prompt = build_quality_judge_prompt(input_data.generated_email)
        raw = await self._language_model_client.generate_content(judge_prompt)
        judge_value, judge_details = _parse_quality_judge(raw)

        value = round((0.4 * automated) + (0.6 * judge_value), 4)
        details = (
            f"Automated={automated:.2f} ({automated_details}). "
            f"Judge={judge_value:.2f} ({judge_details})"
        )

        return MetricScore(name=self.name, value=value, details=details)
