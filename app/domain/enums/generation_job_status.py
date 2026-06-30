"""Generation job status values."""

from enum import Enum


class GenerationJobStatus(str, Enum):
    """Lifecycle states for async generation jobs."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
