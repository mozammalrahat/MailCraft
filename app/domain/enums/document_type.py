"""Application document type values."""

from enum import StrEnum


class DocumentType(StrEnum):
    """Document type axis for application documents."""

    EMAIL = "email"
    COVER_LETTER = "cover_letter"
