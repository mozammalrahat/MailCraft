import csv
import json
from pathlib import Path

from app.schemas.evaluation import EvaluationReport

REPORTS_DIR = Path(__file__).resolve().parents[3] / "reports"


def write_json_report(report: EvaluationReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return path


def write_csv_summary(report: EvaluationReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    metric_names = [metric.name for metric in report.metadata.metrics]

    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["scenario_id", "strategy", *metric_names],
        )
        writer.writeheader()

        for strategy_key, strategy_result in report.strategies.items():
            for scenario in strategy_result.scenarios:
                row = {
                    "scenario_id": scenario.scenario_id,
                    "strategy": strategy_key,
                }
                row.update(scenario.scores)
                writer.writerow(row)

    return path


def write_comparison_report(
    report: EvaluationReport, path: Path
) -> Path:
    comparison: dict[str, object] = {
        "generated_at": report.metadata.generated_at.isoformat(),
        "strategies": {},
    }

    for strategy_key, strategy_result in report.strategies.items():
        comparison["strategies"][strategy_key] = {
            "model": strategy_result.model,
            "averages": strategy_result.averages,
        }

    if len(report.strategies) >= 2:
        keys = list(report.strategies.keys())
        left, right = keys[0], keys[1]
        left_avg = report.strategies[left].averages
        right_avg = report.strategies[right].averages
        deltas = {
            metric: round(left_avg.get(metric, 0.0) - right_avg.get(metric, 0.0), 4)
            for metric in left_avg
        }
        comparison["deltas"] = {
            "baseline": right,
            "candidate": left,
            "metric_deltas": deltas,
        }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    return path


def write_all_reports(
    report: EvaluationReport,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    base_dir = output_dir or REPORTS_DIR
    written: dict[str, Path] = {}

    for strategy_key in report.strategies:
        strategy_report = EvaluationReport(
            metadata=report.metadata,
            strategies={strategy_key: report.strategies[strategy_key]},
            summary=report.summary,
        )
        written[f"evaluation_{strategy_key}.json"] = write_json_report(
            strategy_report,
            base_dir / f"evaluation_{strategy_key}.json",
        )

    written["evaluation_full.json"] = write_json_report(
        report, base_dir / "evaluation_full.json"
    )
    written["evaluation_summary.csv"] = write_csv_summary(
        report, base_dir / "evaluation_summary.csv"
    )
    written["evaluation_comparison.json"] = write_comparison_report(
        report, base_dir / "evaluation_comparison.json"
    )
    return written
