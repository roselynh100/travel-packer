"""Shared helpers for optional float handling (avoid repeated None checks)."""

from typing import Optional


def gt(value: Optional[float], threshold: float) -> bool:
    """True iff value is not None and value > threshold."""
    return value is not None and value > threshold


def lt(value: Optional[float], threshold: float) -> bool:
    """True iff value is not None and value < threshold."""
    return value is not None and value < threshold


def over_limit(*, current: float, additional: Optional[float], limit: float) -> bool:
    """True iff additional is not None and (current + additional) > limit."""
    return additional is not None and (current + additional) > limit


def all_present(*values: Optional[float]) -> bool:
    """True iff all values are not None."""
    return all(v is not None for v in values)


def default(value: Optional[float], fallback: float) -> float:
    """Return value if not None, else fallback."""
    return value if value is not None else fallback
