#!/usr/bin/env python3
"""Run MailCraft evaluation across all scenarios and strategies."""

import asyncio
import logging

from app.config import get_settings
from app.logging_config import configure_logging
from app.services.evaluation.report_writer import write_all_reports
from app.services.evaluation.runner import run_full_evaluation
from app.services.llm.client import LlmClient


async def main() -> int:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    if not settings.google_api_key:
        logging.error(
            "GOOGLE_API_KEY is not configured. Set it in .env before running."
        )
        return 1

    llm_client = LlmClient(settings)
    logging.info("Starting evaluation run")

    report = await run_full_evaluation(llm_client, settings)
    written = write_all_reports(report)

    for path in written.values():
        logging.info("Wrote report artifact: %s", path)

    logging.info(
        "Evaluation complete. Overall average: %.4f",
        report.summary.overall_average,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
