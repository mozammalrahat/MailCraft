"""Email prompting strategy values."""

from enum import StrEnum


class EmailStrategy(StrEnum):
    """Supported legacy email prompting strategies."""

    STRATEGY_A = "strategy_a"
    STRATEGY_B = "strategy_b"
