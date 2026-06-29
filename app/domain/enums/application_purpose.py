"""Application document purpose values."""

from enum import StrEnum


class ApplicationPurpose(StrEnum):
    """Purpose axis for application documents."""

    INTERVIEW = "interview"
    MS = "ms"
    PHD = "phd"
