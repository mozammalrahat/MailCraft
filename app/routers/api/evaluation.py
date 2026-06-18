from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.dependencies import get_llm_client
from app.schemas.evaluation import EvaluationReport
from app.services.evaluation.report_writer import REPORTS_DIR, write_all_reports
from app.services.evaluation.runner import run_full_evaluation
from app.services.llm.client import LlmClient

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

LlmClientDep = Annotated[LlmClient, Depends(get_llm_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/run", response_model=EvaluationReport)
async def run_evaluation_endpoint(
    llm_client: LlmClientDep,
    settings: SettingsDep,
) -> EvaluationReport:
    if not settings.google_api_key:
        raise HTTPException(status_code=400, detail="Google API key is not configured")

    report = await run_full_evaluation(llm_client, settings)
    write_all_reports(report)
    return report


@router.get("/latest")
def get_latest_evaluation_metadata() -> dict[str, object]:
    comparison_path = REPORTS_DIR / "evaluation_comparison.json"
    if not comparison_path.is_file():
        raise HTTPException(status_code=404, detail="No evaluation report found")

    import json

    data = json.loads(comparison_path.read_text(encoding="utf-8"))
    return {
        "report_path": str(comparison_path),
        "comparison": data,
    }
