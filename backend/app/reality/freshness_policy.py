"""Finite numerical predicates for declared observation-age freshness policies.

Only positive, finite numeric windows are valid. Infinities can wrongly
classify arbitrarily old evidence as fresh, while NaN is unordered.
Do not coerce booleans, numeric strings or unrepresentably large integers.
"""
from math import isfinite


def is_finite_number(value: object) -> bool:
    """Return whether an uncoerced int/float can be represented finitely."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return isfinite(value)
    except OverflowError:
        # Extremely large Python integers do not fit in a float.
        return False


def is_positive_finite_number(value: object) -> bool:
    """Use for a caller-declared freshness maximum age in seconds."""
    return is_finite_number(value) and value > 0


def is_nonnegative_finite_number(value: object) -> bool:
    """Use for an elapsed age measurement, allowing exactly zero."""
    return is_finite_number(value) and value >= 0


__all__ = [
    "is_finite_number",
    "is_positive_finite_number",
    "is_nonnegative_finite_number",
]
