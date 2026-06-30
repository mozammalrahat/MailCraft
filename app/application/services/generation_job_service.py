"""Generation job persistence and queueing."""

import json
import logging
from datetime import UTC, datetime

from app.core.configuration import Settings
from app.core.exceptions import ServiceValidationError
from app.database.models.generation_job import GenerationJob
from app.domain.enums.generation_job_status import GenerationJobStatus
from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GenerationJobService:
    """Manage async generation jobs."""

    def __init__(self, database_session: Session) -> None:
        self._database_session = database_session

    def create_job(self, *, user_id: int, kind: str, payload: dict) -> GenerationJob:
        """Persist a queued generation job."""
        job = GenerationJob(
            user_id=user_id,
            status=GenerationJobStatus.QUEUED.value,
            kind=kind,
            payload_json=json.dumps(payload),
        )
        self._database_session.add(job)
        self._database_session.commit()
        self._database_session.refresh(job)
        return job

    def get_owned(self, user_id: int, job_id: str) -> GenerationJob:
        """Return a job owned by the user."""
        job = (
            self._database_session.query(GenerationJob)
            .filter(GenerationJob.id == job_id, GenerationJob.user_id == user_id)
            .first()
        )
        if job is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return job

    def get_by_id(self, job_id: str) -> GenerationJob:
        """Return a job by ID for worker processing."""
        job = (
            self._database_session.query(GenerationJob)
            .filter(GenerationJob.id == job_id)
            .first()
        )
        if job is None:
            raise ServiceValidationError(f"Generation job not found: {job_id}")
        return job

    def mark_running(self, job: GenerationJob) -> None:
        """Mark a job as running."""
        job.status = GenerationJobStatus.RUNNING.value
        job.updated_at = datetime.now(UTC)
        self._database_session.commit()

    def mark_completed(self, job: GenerationJob, *, generation_id: int) -> None:
        """Mark a job completed with a generated content ID."""
        job.status = GenerationJobStatus.COMPLETED.value
        job.result_generation_id = generation_id
        job.error_message = None
        job.updated_at = datetime.now(UTC)
        self._database_session.commit()

    def mark_failed(self, job: GenerationJob, *, error_message: str) -> None:
        """Mark a job failed."""
        job.status = GenerationJobStatus.FAILED.value
        job.error_message = error_message
        job.updated_at = datetime.now(UTC)
        self._database_session.commit()


async def enqueue_generation_job(settings: Settings, job_id: str) -> None:
    """Enqueue a generation job for background processing."""
    if not settings.generation_async_enabled:
        raise ServiceValidationError("Async generation is disabled")

    try:
        from arq import create_pool
        from arq.connections import RedisSettings
    except ImportError as exc:
        raise ServiceValidationError(
            "arq is required when GENERATION_ASYNC_ENABLED=true"
        ) from exc

    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        await redis.enqueue_job("process_generation_job", job_id)
    finally:
        await redis.close()

    logger.info("Enqueued generation job", extra={"job_id": job_id})
