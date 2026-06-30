"""Shared fact-matching logic for humanization guards and eval metrics."""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

_NORMALIZE_PATTERN = re.compile(r"[^\w\s]")
DEFAULT_FACT_MATCH_THRESHOLD = 0.75


def normalize_text(text: str) -> str:
    """Normalize text for fuzzy fact matching."""
    lowered = text.lower().strip()
    return _NORMALIZE_PATTERN.sub(" ", lowered)


def _token_set(text: str) -> set[str]:
    return {token for token in normalize_text(text).split() if token}


def match_fact_in_text(fact: str, text: str) -> float:
    """Return a 0.0-1.0 score for how well a fact appears in text."""
    normalized_fact = normalize_text(fact)
    normalized_text = normalize_text(text)

    if normalized_fact in normalized_text:
        return 1.0

    fact_tokens = _token_set(fact)
    if not fact_tokens:
        return 0.0

    text_tokens = _token_set(text)
    overlap = len(fact_tokens & text_tokens) / len(fact_tokens)

    substring_score = SequenceMatcher(
        None, normalized_fact, normalized_text
    ).ratio()

    return max(overlap, substring_score)


@dataclass(frozen=True)
class FactPreservationResult:
    """Outcome of verifying facts against generated text."""

    matched: list[str]
    missed: list[str]
    score: float


def verify_facts_preserved(
    facts: list[str],
    text: str,
    *,
    threshold: float = DEFAULT_FACT_MATCH_THRESHOLD,
) -> FactPreservationResult:
    """Check which facts appear in text at or above the match threshold."""
    if not facts:
        return FactPreservationResult(matched=[], missed=[], score=1.0)

    matched: list[str] = []
    missed: list[str] = []

    for fact in facts:
        if match_fact_in_text(fact, text) >= threshold:
            matched.append(fact)
        else:
            missed.append(fact)

    score = len(matched) / len(facts)
    return FactPreservationResult(matched=matched, missed=missed, score=score)
