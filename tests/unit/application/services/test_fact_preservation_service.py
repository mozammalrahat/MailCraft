from app.application.services.fact_preservation_service import (
    match_fact_in_text,
    verify_facts_preserved,
)


def test_match_fact_in_text_exact_substring() -> None:
    score = match_fact_in_text(
        "Demo held on May 12",
        "Subject: Follow up\n\nDemo held on May 12.",
    )
    assert score == 1.0


def test_verify_facts_preserved_all_matched() -> None:
    result = verify_facts_preserved(
        ["Demo held on May 12", "Pricing for 50 seats"],
        "Subject: Follow up\n\nDemo held on May 12. Pricing for 50 seats.",
    )
    assert result.score == 1.0
    assert result.missed == []


def test_verify_facts_preserved_partial() -> None:
    result = verify_facts_preserved(
        ["Demo held on May 12", "Pricing for 50 seats"],
        "Subject: Update\n\nDemo held on May 12 only.",
    )
    assert 0.0 < result.score < 1.0
    assert len(result.missed) == 1


def test_verify_facts_preserved_empty_facts() -> None:
    result = verify_facts_preserved([], "Subject: Test\n\nBody")
    assert result.score == 1.0
