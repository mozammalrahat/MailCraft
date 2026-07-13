"""Generation job status values."""

from enum import StrEnum


class GenerationJobStatus(StrEnum):
    """Lifecycle states for async generation jobs."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
