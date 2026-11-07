"""UTC storage helpers and America/Sao_Paulo display conversion."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
DISPLAY_TZ = ZoneInfo("America/Sao_Paulo")


def utc_now() -> datetime:
    """Return the current timezone-aware datetime in UTC."""
    return datetime.now(UTC)


def to_display_tz(value: datetime) -> datetime:
    """Convert a UTC (or naive-as-UTC) datetime to America/Sao_Paulo."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(DISPLAY_TZ)


def to_utc(value: datetime) -> datetime:
    """Normalize any datetime to UTC for persistence."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
