"""
utils/validators.py
Input validation helpers for API routes.
"""

import re
from typing import Optional

_MIN_LEN = 2
_MAX_LEN = 100
_ILLEGAL = re.compile(r"[<>{}\[\]\\|`]")


def validate_keyword(keyword: str) -> Optional[str]:
    """
    Validate a brand / search keyword string.
    Returns an error message if invalid, else None.
    """
    if not keyword:
        return "The 'keyword' query parameter is required."
    if len(keyword) < _MIN_LEN:
        return f"Keyword must be at least {_MIN_LEN} characters long."
    if len(keyword) > _MAX_LEN:
        return f"Keyword must not exceed {_MAX_LEN} characters."
    if _ILLEGAL.search(keyword):
        return "Keyword contains invalid characters."
    return None


def clamp(value, lo: int, hi: int, default: int) -> int:
    """Parse an integer safely and clamp it to [lo, hi]."""
    try:
        return max(lo, min(int(value), hi))
    except (TypeError, ValueError):
        return default
