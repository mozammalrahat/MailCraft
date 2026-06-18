import re
from difflib import SequenceMatcher

from app.services.evaluation.metrics.base import (
    MetricDefinition,
    MetricInput,
    MetricScore,
)

_MATCH_THRESHOLD = 0.75
_NORMALIZE_PATTERN = re.compile(r"[^\w\s]")


def _normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    return _NORMALIZE_PATTERN.sub(" ", lowered)


def _token_set(text: str) -> set[str]:
    return {token for token in _normalize_text(text).split() if token}


def _match_score(fact: str, email: str) -> float:
    normalized_fact = _normalize_text(fact)
    normalized_email = _normalize_text(email)

    if normalized_fact in normalized_email:
        return 1.0

    fact_tokens = _token_set(fact)
    if not fact_tokens:
        return 0.0

    email_tokens = _token_set(email)
    overlap = len(fact_tokens & email_tokens) / len(fact_tokens)

    substring_score = SequenceMatcher(None, normalized_fact, normalized_email).ratio()

    return max(overlap, substring_score)


class FactRecallMetric:
    @property
    def name(self) -> str:
        return "fact_recall"

    @property
    def definition(self) -> MetricDefinition:
        return MetricDefinition(
            name=self.name,
            definition=(
                "Measures how many required key facts appear in the generated email."
            ),
            logic=(
                "For each key fact, normalize text and compute token overlap plus "
                f"fuzzy substring similarity. A fact is matched when score >= "
                f"{_MATCH_THRESHOLD}. Score = matched_facts / total_facts."
            ),
            technique="automated",
        )

    async def score(self, input_data: MetricInput) -> MetricScore:
        if not input_data.key_facts:
            return MetricScore(name=self.name, value=1.0, details="No facts to check.")

        matched: list[str] = []
        missed: list[str] = []

        for fact in input_data.key_facts:
            if _match_score(fact, input_data.generated_email) >= _MATCH_THRESHOLD:
                matched.append(fact)
            else:
                missed.append(fact)

        value = len(matched) / len(input_data.key_facts)
        details = f"Matched {len(matched)}/{len(input_data.key_facts)} facts."
        if missed:
            details += f" Missed: {'; '.join(missed)}"

        return MetricScore(name=self.name, value=round(value, 4), details=details)
