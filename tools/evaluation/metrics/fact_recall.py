from app.application.services.fact_preservation_service import (
    DEFAULT_FACT_MATCH_THRESHOLD,
    verify_facts_preserved,
)

from tools.evaluation.metrics.base import (
    MetricDefinition,
    MetricInput,
    MetricScore,
)


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
                f"{DEFAULT_FACT_MATCH_THRESHOLD}. Score = matched_facts / total_facts."
            ),
            technique="automated",
        )

    async def score(self, input_data: MetricInput) -> MetricScore:
        if not input_data.key_facts:
            return MetricScore(name=self.name, value=1.0, details="No facts to check.")

        result = verify_facts_preserved(
            input_data.key_facts,
            input_data.generated_email,
        )

        details = (
            f"Matched {len(result.matched)}/{len(input_data.key_facts)} facts."
        )
        if result.missed:
            details += f" Missed: {'; '.join(result.missed)}"

        return MetricScore(
            name=self.name,
            value=round(result.score, 4),
            details=details,
        )
