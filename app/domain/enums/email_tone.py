"""Email tone values for legacy generation."""

from enum import StrEnum


class EmailTone(StrEnum):
    """Supported email tones."""

    FORMAL = "formal"
    CASUAL = "casual"
    URGENT = "urgent"
    EMPATHETIC = "empathetic"
