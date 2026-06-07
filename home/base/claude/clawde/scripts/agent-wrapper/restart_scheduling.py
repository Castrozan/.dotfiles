import datetime
import time

INITIAL_RESTART_DELAY_SECONDS = 10
MAXIMUM_RESTART_DELAY_SECONDS = 300
STABLE_RUNTIME_THRESHOLD_SECONDS = 60


def is_within_active_hours(
    active_hours_start: int | None,
    active_hours_end: int | None,
    now: datetime.datetime | None = None,
) -> bool:
    if active_hours_start is None:
        return True
    if now is None:
        now = datetime.datetime.now()
    current_hour = now.hour
    if active_hours_start <= active_hours_end:
        return active_hours_start <= current_hour < active_hours_end
    return current_hour >= active_hours_start or current_hour < active_hours_end


def seconds_until_active_hours_start(
    active_hours_start: int,
    now: datetime.datetime | None = None,
) -> int:
    if now is None:
        now = datetime.datetime.now()
    target = now.replace(hour=active_hours_start, minute=0, second=0, microsecond=0)
    if target <= now and now.hour != active_hours_start:
        target += datetime.timedelta(days=1)
    return max(1, int((target - now).total_seconds()))


def should_rotate_session(
    daily_session_rotation: bool, last_fresh_start_date: str | None
) -> bool:
    if not daily_session_rotation:
        return False
    if last_fresh_start_date is None:
        return False
    today = time.strftime("%Y-%m-%d")
    return last_fresh_start_date != today


def should_reset_backoff(
    runtime_seconds: float,
    was_stuck_kill: bool,
    stable_runtime_threshold_seconds: int = STABLE_RUNTIME_THRESHOLD_SECONDS,
) -> bool:
    if was_stuck_kill:
        return False
    return runtime_seconds > stable_runtime_threshold_seconds
