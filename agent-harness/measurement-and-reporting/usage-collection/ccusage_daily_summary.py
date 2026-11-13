from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date

CCUSAGE_USAGE_SOURCE = "ccusage-offline"
CANONICAL_CALENDAR_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class CcusageDocumentError(ValueError):
    pass


@dataclass(frozen=True)
class ModelDailyBreakdown:
    model_name: str
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
    cost_usd: float

    def token_total(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_input_tokens
            + self.cache_creation_input_tokens
        )


@dataclass(frozen=True)
class CalendarDayUsage:
    date_text: str
    model_breakdowns: tuple[ModelDailyBreakdown, ...]


def summarize_ccusage_daily(ccusage_daily_document) -> dict | None:
    calendar_days = parse_calendar_days(ccusage_daily_document)
    if not calendar_days:
        return None
    breakdowns_by_model = group_breakdowns_by_model(calendar_days)
    date_texts = [day.date_text for day in calendar_days]
    return {
        "model_usage_totals": {
            model_name: model_usage_totals(breakdowns_by_model[model_name])
            for model_name in sorted(breakdowns_by_model)
        },
        "daily_model_tokens": daily_model_tokens(calendar_days),
        "stats_last_computed_date": max(date_texts),
        "model_usage_first_date": min(date_texts),
        "model_usage_source": CCUSAGE_USAGE_SOURCE,
    }


def parse_calendar_days(ccusage_daily_document) -> list[CalendarDayUsage]:
    raw_days = raw_daily_list(ccusage_daily_document)
    calendar_days = [parse_calendar_day(raw_day) for raw_day in raw_days]
    date_texts = [day.date_text for day in calendar_days]
    if len(set(date_texts)) != len(date_texts):
        raise CcusageDocumentError("ccusage daily output repeats a calendar date")
    return sorted(calendar_days, key=lambda day: day.date_text)


def raw_daily_list(ccusage_daily_document) -> list:
    if not isinstance(ccusage_daily_document, dict):
        raise CcusageDocumentError("ccusage daily output must be a JSON object")
    raw_days = ccusage_daily_document.get("daily")
    if not isinstance(raw_days, list):
        raise CcusageDocumentError("ccusage daily output must carry a daily list")
    return raw_days


def parse_calendar_day(raw_day) -> CalendarDayUsage:
    if not isinstance(raw_day, dict):
        raise CcusageDocumentError("ccusage daily entry must be a JSON object")
    date_text = raw_day.get("date")
    if not is_canonical_calendar_date(date_text):
        raise CcusageDocumentError(
            f"ccusage daily date {date_text!r} must be a canonical YYYY-MM-DD date"
        )
    raw_breakdowns = raw_day.get("modelBreakdowns")
    if not isinstance(raw_breakdowns, list):
        raise CcusageDocumentError(
            f"daily entry {date_text} must carry modelBreakdowns"
        )
    breakdowns = tuple(
        parse_model_breakdown(date_text, raw_breakdown)
        for raw_breakdown in raw_breakdowns
    )
    model_names = [breakdown.model_name for breakdown in breakdowns]
    if len(set(model_names)) != len(model_names):
        raise CcusageDocumentError(f"daily entry {date_text} repeats a model")
    return CalendarDayUsage(date_text=date_text, model_breakdowns=breakdowns)


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


def parse_model_breakdown(date_text: str, raw_breakdown) -> ModelDailyBreakdown:
    if not isinstance(raw_breakdown, dict):
        raise CcusageDocumentError(f"model breakdown on {date_text} must be an object")
    model_name = raw_breakdown.get("modelName")
    if not isinstance(model_name, str) or not model_name:
        raise CcusageDocumentError(
            f"model breakdown on {date_text} must name its model"
        )
    context = f"{model_name} on {date_text}"
    return ModelDailyBreakdown(
        model_name=model_name,
        input_tokens=nonnegative_integer(raw_breakdown, "inputTokens", context),
        output_tokens=nonnegative_integer(raw_breakdown, "outputTokens", context),
        cache_read_input_tokens=nonnegative_integer(
            raw_breakdown, "cacheReadTokens", context
        ),
        cache_creation_input_tokens=nonnegative_integer(
            raw_breakdown, "cacheCreationTokens", context
        ),
        cost_usd=finite_nonnegative_amount(raw_breakdown, "cost", context),
    )


def nonnegative_integer(raw_breakdown: dict, field_name: str, context: str) -> int:
    value = raw_breakdown.get(field_name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CcusageDocumentError(
            f"{field_name} for {context} must be a nonnegative integer"
        )
    return value


def finite_nonnegative_amount(
    raw_breakdown: dict, field_name: str, context: str
) -> float:
    value = raw_breakdown.get(field_name)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise CcusageDocumentError(
            f"{field_name} for {context} must be a finite nonnegative number"
        )
    return float(value)


def group_breakdowns_by_model(
    calendar_days: list[CalendarDayUsage],
) -> dict[str, list[ModelDailyBreakdown]]:
    grouped: dict[str, list[ModelDailyBreakdown]] = {}
    for day in calendar_days:
        for breakdown in day.model_breakdowns:
            grouped.setdefault(breakdown.model_name, []).append(breakdown)
    return grouped


def model_usage_totals(breakdowns: list[ModelDailyBreakdown]) -> dict:
    return {
        "input_tokens": sum(breakdown.input_tokens for breakdown in breakdowns),
        "output_tokens": sum(breakdown.output_tokens for breakdown in breakdowns),
        "cache_read_input_tokens": sum(
            breakdown.cache_read_input_tokens for breakdown in breakdowns
        ),
        "cache_creation_input_tokens": sum(
            breakdown.cache_creation_input_tokens for breakdown in breakdowns
        ),
        "cost_usd": math.fsum(breakdown.cost_usd for breakdown in breakdowns),
    }


def daily_model_tokens(calendar_days: list[CalendarDayUsage]) -> list[dict]:
    return [
        {
            "date": day.date_text,
            "tokens_by_model": {
                breakdown.model_name: breakdown.token_total()
                for breakdown in sorted(
                    day.model_breakdowns, key=lambda item: item.model_name
                )
            },
        }
        for day in calendar_days
    ]
