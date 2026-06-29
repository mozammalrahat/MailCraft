import json
from pathlib import Path

from app.schemas.evaluation import Scenario, ScenarioCollection

DEFAULT_SCENARIOS_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "scenarios" / "scenarios.json"
)
REQUIRED_SCENARIO_COUNT = 10


def load_scenarios(
    path: Path | None = None,
    *,
    required_count: int | None = REQUIRED_SCENARIO_COUNT,
) -> list[Scenario]:
    scenarios_path = path or DEFAULT_SCENARIOS_PATH

    if not scenarios_path.is_file():
        msg = f"Scenarios file not found: {scenarios_path}"
        raise FileNotFoundError(msg)

    raw = json.loads(scenarios_path.read_text(encoding="utf-8"))
    collection = ScenarioCollection.model_validate(raw)

    if required_count is not None and collection.count != required_count:
        msg = f"Expected {required_count} scenarios, found {collection.count}"
        raise ValueError(msg)

    return collection.scenarios
