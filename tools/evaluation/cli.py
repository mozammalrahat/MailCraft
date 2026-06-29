"""CLI entrypoint for running the evaluation pipeline."""

import asyncio
import logging

from app.core.configuration import get_settings
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.logging_config import configure_logging

from tools.evaluation.report_writer import write_all_reports
from tools.evaluation.runner import run_full_evaluation

_EVALUATION_DEFAULT_REQUEST_DELAY_SECONDS = 20


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
        else _EVALUATION_DEFAULT_REQUEST_DELAY_SECONDS
    )
    language_model_client = LargeLanguageModelClient(
        settings, request_delay_seconds=request_delay
    )
    logging.info(
        "Starting evaluation run (%.1fs delay between LLM requests)",
        request_delay,
    )

    report = await run_full_evaluation(language_model_client, settings)
    written = write_all_reports(report)

    for path in written.values():
        logging.info("Wrote report artifact: %s", path)

    logging.info(
        "Evaluation complete. Overall average: %.4f",
        report.summary.overall_average,
    )
    return 0


def main() -> int:
    """Run evaluation CLI."""
    return asyncio.run(_async_main())
