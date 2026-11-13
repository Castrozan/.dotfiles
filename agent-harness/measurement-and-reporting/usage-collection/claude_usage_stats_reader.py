from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

MEASURED_ACTIVITY_COUNTER_FIELDS = {
    "messageCount": "message_count",
    "sessionCount": "session_count",
    "toolCallCount": "tool_call_count",
}
CANONICAL_CALENDAR_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def default_stats_cache_path() -> Path:
    return Path.home() / ".claude" / "stats-cache.json"


def read_stats_cache(stats_cache_path: Path) -> dict:
    if not stats_cache_path.is_file():
        return {}
    try:
        parsed_stats_cache = json.loads(stats_cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    return parsed_stats_cache if isinstance(parsed_stats_cache, dict) else {}


def first_session_calendar_date(stats_cache: dict) -> str | None:
    raw_first_session_date = stats_cache.get("firstSessionDate") or ""
    return raw_first_session_date[:10] or None


def is_canonical_calendar_date(value) -> bool:
    if not isinstance(value, str):
        return False
    if CANONICAL_CALENDAR_DATE_PATTERN.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_nonnegative_integer(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def is_measured_daily_activity(daily_entry) -> bool:
    return (
        isinstance(daily_entry, dict)
        and is_canonical_calendar_date(daily_entry.get("date"))
        and all(
            is_nonnegative_integer(daily_entry.get(counter_field))
            for counter_field in MEASURED_ACTIVITY_COUNTER_FIELDS
        )
    )


def extract_complete_measured_daily_activity(stats_cache: dict) -> list[dict] | None:
    daily_entries = stats_cache.get("dailyActivity")
    if not isinstance(daily_entries, list):
        return None
    if not all(
        is_measured_daily_activity(daily_entry) for daily_entry in daily_entries
    ):
        return None
    return [
        {
            "date": daily_entry["date"],
            **{
                snake_case_field: daily_entry[camel_case_field]
                for camel_case_field, snake_case_field in MEASURED_ACTIVITY_COUNTER_FIELDS.items()
            },
        }
        for daily_entry in daily_entries
    ]


def activity_last_computed_date(stats_cache: dict) -> str | None:
    last_computed_date = stats_cache.get("lastComputedDate")
    return (
        last_computed_date if is_canonical_calendar_date(last_computed_date) else None
    )


def summarize_stats_cache(stats_cache: dict) -> dict:
    summary = {
        "stats_first_session_date": first_session_calendar_date(stats_cache),
        "activity_last_computed_date": activity_last_computed_date(stats_cache),
    }
    daily_activity = extract_complete_measured_daily_activity(stats_cache)
    if daily_activity is not None:
        summary["daily_activity"] = daily_activity
    return summary
