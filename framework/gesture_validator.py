"""Pure argument validation for gestures; testable without a device."""
from __future__ import annotations

import math
from typing import Optional

DIRECTIONS = frozenset({"up", "down", "left", "right"})


def validate_direction(direction: Optional[str]) -> str:
    if direction is None or direction.strip().lower() not in DIRECTIONS:
        raise ValueError(f"Direction must be one of {sorted(DIRECTIONS)} but was '{direction}'")
    return direction.strip().lower()


def validate_percent(percent: float) -> float:
    """Percent must be in (0, 1]. NaN fails every comparison, so it is checked explicitly."""
    if math.isnan(percent) or percent <= 0.0 or percent > 1.0:
        raise ValueError(f"Swipe percent must be in (0, 1] but was {percent}")
    return percent


def validate_max_attempts(attempts: int) -> int:
    if attempts < 1:
        raise ValueError(f"maxAttempts must be >= 1 but was {attempts}")
    return attempts
