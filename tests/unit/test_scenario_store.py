from pathlib import Path
import json

import pytest
from app.services.evaluation.scenario_store import (
    REQUIRED_SCENARIO_COUNT,
    load_scenarios,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_SCENARIOS_PATH = FIXTURES_DIR / "sample_scenarios.json"
MAIN_SCENARIOS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "scenarios"
    / "scenarios.json"
)


def test_load_sample_scenarios_fixture() -> None:
    scenarios = load_scenarios(SAMPLE_SCENARIOS_PATH, required_count=2)
    assert len(scenarios) == 2
    assert scenarios[0].id == "s01"
    assert scenarios[0].tone.value == "formal"


def test_load_main_scenarios_has_ten_entries() -> None:
    scenarios = load_scenarios(MAIN_SCENARIOS_PATH)
    assert len(scenarios) == REQUIRED_SCENARIO_COUNT
    assert len({scenario.id for scenario in scenarios}) == REQUIRED_SCENARIO_COUNT


def test_load_scenarios_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_scenarios(Path("/nonexistent/scenarios.json"))


def test_load_scenarios_wrong_count(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(
        json.dumps(
            {
                "scenarios": [
                    {
                        "id": "s99",
                        "intent": "Test",
                        "key_facts": ["Fact"],
                        "tone": "formal",
                        "reference_email": "Subject: Test\n\nBody",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Expected 10 scenarios"):
        load_scenarios(bad_file)
