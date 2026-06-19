"""CLI entrypoint for running the evaluation pipeline."""

import asyncio
import logging

from app.config import get_settings
from app.logging_config import configure_logging
from app.services.evaluation.report_writer import write_all_reports
from app.services.evaluation.runner import run_full_evaluation
from app.services.llm.client import LlmClient

_EVAL_DEFAULT_REQUEST_DELAY_SECONDS = 20


async def _async_main() -> int:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    if not settings.google_api_key:
        logging.error(
            "GOOGLE_API_KEY is not configured. Set it in .env before running."
        )
        return 1

    request_delay = (
        settings.llm_request_delay_seconds
        if settings.llm_request_delay_seconds > 0
        else _EVAL_DEFAULT_REQUEST_DELAY_SECONDS
    )
    llm_client = LlmClient(settings, request_delay_seconds=request_delay)
    logging.info(
        "Starting evaluation run (%.1fs delay between LLM requests)",
        request_delay,
    )

    report = await run_full_evaluation(llm_client, settings)
    written = write_all_reports(report)

    for path in written.values():
        logging.info("Wrote report artifact: %s", path)

    logging.info(
        "Evaluation complete. Overall average: %.4f",
        report.summary.overall_average,
    )
    return 0


def main() -> int:
    return asyncio.run(_async_main())
