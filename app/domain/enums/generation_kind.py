"""Generation kind discriminator for persisted content."""

from enum import StrEnum


class GenerationKind(StrEnum):
    """Discriminator for unified generated content records."""

    LEGACY_EMAIL = "legacy_email"
    APPLICATION_DOCUMENT = "application_document"
