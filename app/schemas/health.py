"""Health check response schemas."""

from typing import Literal

from pydantic import BaseModel

HealthStatus = Literal["ok", "degraded", "fail"]
CheckStatus = Literal["ok", "fail", "skipped"]


class HealthCheckResult(BaseModel):
    """Aggregated health check response."""

    status: HealthStatus
    checks: dict[str, CheckStatus]
