from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from speech_text import sanitize_speech

SPEAKABLE_FLAGS = (True, True, False, False)


def quiet_hours(now: datetime | None = None) -> bool:
    try:
        instant = now if now is not None else datetime.now(timezone.utc)
        if instant.tzinfo is None or instant.utcoffset() is None:
            return True
        local_hour = instant.astimezone(ZoneInfo("America/Sao_Paulo")).hour
    except (AttributeError, TypeError, ValueError, ZoneInfoNotFoundError):
        return True
    return local_hour >= 17 or local_hour < 9


def prepare_spoken_notification(
    message: str,
    *,
    now: datetime | None = None,
    critical: bool | None = None,
    all_stewards_unable: bool | None = None,
    work_in_progress: bool | None = None,
    duplicate: bool | None = None,
) -> str | None:
    if quiet_hours(now):
        return None
    flags = (critical, all_stewards_unable, work_in_progress, duplicate)
    if not all(
        flag is required for flag, required in zip(flags, SPEAKABLE_FLAGS, strict=True)
    ):
        return None
    return sanitize_speech(message)
