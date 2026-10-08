from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from speech_text import sanitize_speech


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
    if critical is not True or all_stewards_unable is not True:
        return None
    if work_in_progress is not False or duplicate is not False:
        return None
    return sanitize_speech(message)
