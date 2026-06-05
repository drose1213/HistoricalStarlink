"""Shared backend utilities."""

from datetime import datetime
from typing import Optional


def iso_utc(dt: Optional[datetime]) -> Optional[str]:
    """Serialize a naive UTC datetime to ISO 8601 with explicit `Z` suffix.

    Backend stores naive datetimes via ``datetime.utcnow()``; ``str(dt)`` would
    emit ``2026-06-05 01:43:42.123456`` (no timezone), which JavaScript
    ``new Date(...)`` interprets as *local* time, producing an 8-hour drift on
    UTC+8 clients.  Emitting the trailing ``Z`` makes the frontend parse it as
    a UTC instant, which can then be formatted to the user's local zone.
    """
    if dt is None:
        return None
    # Normalize to UTC if the datetime carries a tzinfo; truncate microseconds
    # for stable display rendering.
    if dt.tzinfo is not None:
        from datetime import timezone
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(microsecond=0).isoformat() + "Z"
