# utils/clock.py

from datetime import datetime, timezone


def utcnow() -> datetime:
    """
    Returns timezone-aware UTC timestamp.
    """
    return datetime.now(timezone.utc)