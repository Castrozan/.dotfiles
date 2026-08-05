from __future__ import annotations

import json
from pathlib import Path


def default_stats_cache_path() -> Path:
    return Path.home() / ".claude" / "stats-cache.json"


def read_stats_cache(stats_cache_path: Path) -> dict:
    if not stats_cache_path.is_file():
        return {}
    try:
        return json.loads(stats_cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def extract_daily_model_tokens(stats_cache: dict) -> list[dict]:
    daily_model_tokens = []
    for daily_entry in stats_cache.get("dailyModelTokens", []):
        daily_model_tokens.append(
            {
                "date": daily_entry.get("date"),
                "tokens_by_model": dict(daily_entry.get("tokensByModel", {})),
            }
        )
    return daily_model_tokens


def extract_daily_activity(stats_cache: dict) -> list[dict]:
    daily_activity = []
    for daily_entry in stats_cache.get("dailyActivity", []):
        daily_activity.append(
            {
                "date": daily_entry.get("date"),
                "message_count": daily_entry.get("messageCount", 0),
                "session_count": daily_entry.get("sessionCount", 0),
                "tool_call_count": daily_entry.get("toolCallCount", 0),
            }
        )
    return daily_activity


def extract_model_usage_totals(stats_cache: dict) -> dict:
    model_usage_totals = {}
    for model_name, model_usage in stats_cache.get("modelUsage", {}).items():
        model_usage_totals[model_name] = {
            "input_tokens": model_usage.get("inputTokens", 0),
            "output_tokens": model_usage.get("outputTokens", 0),
            "cache_read_input_tokens": model_usage.get("cacheReadInputTokens", 0),
            "cache_creation_input_tokens": model_usage.get(
                "cacheCreationInputTokens", 0
            ),
            "cost_usd": model_usage.get("costUSD", 0),
        }
    return model_usage_totals


def first_session_calendar_date(stats_cache: dict) -> str | None:
    raw_first_session_date = stats_cache.get("firstSessionDate") or ""
    return raw_first_session_date[:10] or None


def summarize_stats_cache(stats_cache: dict) -> dict:
    return {
        "stats_first_session_date": first_session_calendar_date(stats_cache),
        "stats_last_computed_date": stats_cache.get("lastComputedDate"),
        "daily_model_tokens": extract_daily_model_tokens(stats_cache),
        "daily_activity": extract_daily_activity(stats_cache),
        "model_usage_totals": extract_model_usage_totals(stats_cache),
    }
