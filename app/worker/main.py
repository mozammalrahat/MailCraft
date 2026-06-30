"""Background generation worker entrypoint."""

import asyncio
import base64
import json
import logging

from app.application.handlers.application_document_handler import (
    ApplicationDocumentHandler,
)
from app.application.handlers.email_generation_handler import EmailGenerationHandler
from app.application.services.generation_job_service import GenerationJobService
from app.core.configuration import get_settings
from app.core.exceptions import ServiceValidationError
from app.database.engine_manager import get_database_engine_manager, initialize_database
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.email_strategy import EmailStrategy
from app.domain.enums.email_tone import EmailTone
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.infrastructure.storage.factory import build_file_storage
from app.schemas.email_generation import EmailGenerationRequest

logger = logging.getLogger(__name__)


async def startup(ctx: dict) -> None:
    """ARQ on_startup hook: initialise the DB engine once per worker process."""
    del ctx
    initialize_database()
    logger.info("Worker: database initialised")


async def process_generation_job(ctx: dict, job_id: str) -> dict[str, str | int | None]:
    """Worker entrypoint for queued generation jobs."""
    del ctx
    settings = get_settings()
    session_factory = get_database_engine_manager().get_session_factory()
    session = session_factory()
    job_service = GenerationJobService(session)
    language_model_client = LargeLanguageModelClient(settings)
    file_storage = build_file_storage(settings)

    try:
        job = job_service.get_by_id(job_id)

        # Idempotency guard: skip already-completed jobs on ARQ retry
        from app.domain.enums.generation_job_status import GenerationJobStatus
        if job.status == GenerationJobStatus.COMPLETED.value:
            logger.info("Job already completed, skipping", extra={"job_id": job_id})
            return {"job_id": job_id, "generation_id": job.generation_id}

        job_service.mark_running(job)
        payload = json.loads(job.payload_json)

        if job.kind == GenerationKind.LEGACY_EMAIL.value:
            request = EmailGenerationRequest(
                intent=payload["intent"],
                key_facts=payload["key_facts"],
                tone=EmailTone(payload["tone"]),
                strategy=EmailStrategy(payload.get("strategy", "strategy_a")),
            )
            handler = EmailGenerationHandler()
            result = await handler.generate_from_api(
                request=request,
                user_id=job.user_id,
                database_session=session,
                settings=settings,
                language_model_client=language_model_client,
            )
            generation_id = result.generated_content_id
        elif job.kind == GenerationKind.APPLICATION_DOCUMENT.value:
            resume_payloads = [
                (
                    item["filename"],
                    base64.b64decode(item["content_base64"]),
                )
                for item in payload.get("resume_files", [])
            ]
            handler = ApplicationDocumentHandler()
            result = await handler.generate(
                user_id=job.user_id,
                purpose=ApplicationPurpose(payload["purpose"]),
                document_type=DocumentType(payload["document_type"]),
                scenario_id=payload["scenario_id"],
                position_description=payload["position_description"],
                resume_file_payloads=resume_payloads,
                grounding_links=payload.get("grounding_links", []),
                database_session=session,
                settings=settings,
                language_model_client=language_model_client,
                file_storage=file_storage,
            )
            generation_id = result.id
        else:
            raise ServiceValidationError(f"Unsupported job kind: {job.kind}")

        if generation_id is None:
            raise ServiceValidationError("Generation did not persist a record")

        job_service.mark_completed(job, generation_id=generation_id)
        logger.info(
            "Generation job completed",
            extra={"job_id": job_id, "generation_id": generation_id},
        )
        return {"job_id": job_id, "generation_id": generation_id}
    except Exception as exc:
        session.rollback()
        try:
            job = job_service.get_by_id(job_id)
            job_service.mark_failed(job, error_message=str(exc))
        except Exception:
            logger.exception("Failed to mark job as failed", extra={"job_id": job_id})
        logger.warning(
            "Generation job failed",
            extra={"job_id": job_id, "error": str(exc)},
        )
        raise
    finally:
        session.close()


async def run_worker() -> None:
    """Run the ARQ worker process."""
    from arq import run_worker as arq_run_worker
    from arq.connections import RedisSettings

    settings = get_settings()

    class WorkerSettings:
        functions = [process_generation_job]
        on_startup = startup
        redis_settings = RedisSettings.from_dsn(settings.redis_url)

    await arq_run_worker(WorkerSettings)


def main() -> None:
    """CLI entrypoint for mailcraft-worker."""
    from app.core.logging.setup import configure_logging

    configure_logging(settings=get_settings())
    asyncio.run(run_worker())
