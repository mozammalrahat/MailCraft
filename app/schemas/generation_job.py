"""Generation job API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums.generation_job_status import GenerationJobStatus


class GenerationJobResponse(BaseModel):
    """Serialized generation job for polling."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: GenerationJobStatus
    kind: str
    result_generation_id: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class GenerationJobEnqueueResponse(BaseModel):
    """Response when a generation job is queued."""

    job_id: str
    status: GenerationJobStatus
