from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SNAPSHOT_DIRECTORY = Path("agents/usage/snapshots")
AGGREGATE_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "cost_usd",
)


def read_usage_snapshots(snapshot_directory: Path) -> list[dict]:
    if not snapshot_directory.is_dir():
        return []
    usage_snapshots = []
    for snapshot_path in sorted(snapshot_directory.glob("*.json")):
        try:
            usage_snapshots.append(json.loads(snapshot_path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return usage_snapshots


def sum_model_usage_totals(model_usage_totals_list: list[dict]) -> dict:
    summed_model_usage_totals: dict[str, dict] = {}
    for model_usage_totals in model_usage_totals_list:
        for model_name, model_totals in model_usage_totals.items():
            accumulated = summed_model_usage_totals.setdefault(model_name, {})
            for field_name, field_value in model_totals.items():
                accumulated[field_name] = accumulated.get(field_name, 0) + field_value
    return summed_model_usage_totals


def aggregate_token_fields(model_usage_totals: dict) -> dict:
    return {
        field_name: sum(
            model_totals.get(field_name, 0)
            for model_totals in model_usage_totals.values()
        )
        for field_name in AGGREGATE_TOKEN_FIELDS
    }


def combine_daily_total_tokens(daily_model_tokens_list: list[list]) -> dict:
    daily_total_tokens: dict[str, int] = {}
    for daily_model_tokens in daily_model_tokens_list:
        for daily_entry in daily_model_tokens:
            entry_date = daily_entry.get("date")
            if not entry_date:
                continue
            daily_total_tokens[entry_date] = daily_total_tokens.get(
                entry_date, 0
            ) + sum(daily_entry.get("tokens_by_model", {}).values())
    return daily_total_tokens


def sum_memory_recall_savings(memory_recall_savings_list: list[dict]) -> dict:
    suppressed_event_count_by_reason: dict[str, int] = {}
    summed = {
        "memory_recall_session_count": 0,
        "injected_recall_event_count": 0,
        "injected_recall_character_total": 0,
        "suppressed_recall_event_total": 0,
        "dedup_suppressed_character_total": 0,
    }
    for memory_recall_savings in memory_recall_savings_list:
        for scalar_field in summed:
            summed[scalar_field] += memory_recall_savings.get(scalar_field, 0)
        for reason, count in memory_recall_savings.get(
            "suppressed_recall_event_count_by_reason", {}
        ).items():
            suppressed_event_count_by_reason[reason] = (
                suppressed_event_count_by_reason.get(reason, 0) + count
            )
    summed["suppressed_recall_event_count_by_reason"] = suppressed_event_count_by_reason
    return summed


def _earliest(date_values: list) -> str | None:
    present = sorted(value for value in date_values if value)
    return present[0] if present else None


def _latest(date_values: list) -> str | None:
    present = sorted(value for value in date_values if value)
    return present[-1] if present else None


def group_snapshots_by_account(usage_snapshots: list[dict]) -> list[dict]:
    snapshots_by_account: dict[str, list] = {}
    for usage_snapshot in usage_snapshots:
        snapshots_by_account.setdefault(
            usage_snapshot.get("account_label", "unknown"), []
        ).append(usage_snapshot)
    account_views = []
    for account_label in sorted(snapshots_by_account):
        account_snapshots = snapshots_by_account[account_label]
        model_usage_totals = sum_model_usage_totals(
            [s.get("model_usage_totals", {}) for s in account_snapshots]
        )
        account_views.append(
            {
                "account_label": account_label,
                "machine_count": len(
                    {s.get("machine_label") for s in account_snapshots}
                ),
                "model_usage_totals": model_usage_totals,
                "token_totals": aggregate_token_fields(model_usage_totals),
                "daily_total_tokens": combine_daily_total_tokens(
                    [s.get("daily_model_tokens", []) for s in account_snapshots]
                ),
                "memory_recall_savings": sum_memory_recall_savings(
                    [s.get("memory_recall_savings", {}) for s in account_snapshots]
                ),
                "first_session_date": _earliest(
                    [s.get("stats_first_session_date") for s in account_snapshots]
                ),
                "last_computed_date": _latest(
                    [s.get("stats_last_computed_date") for s in account_snapshots]
                ),
            }
        )
    return account_views


def build_chart_series(account_views: list[dict]) -> dict:
    chart_dates = sorted(
        {
            entry_date
            for account_view in account_views
            for entry_date in account_view["daily_total_tokens"]
        }
    )
    series = [
        {
            "account_label": account_view["account_label"],
            "values": [
                account_view["daily_total_tokens"].get(entry_date)
                for entry_date in chart_dates
            ],
        }
        for account_view in account_views
    ]
    return {"dates": chart_dates, "series": series}


def summarize_accounts(account_views: list[dict]) -> dict:
    combined_model_usage = sum_model_usage_totals(
        [account_view["model_usage_totals"] for account_view in account_views]
    )
    combined_savings = sum_memory_recall_savings(
        [account_view["memory_recall_savings"] for account_view in account_views]
    )
    return {
        "account_count": len(account_views),
        "machine_count": sum(
            account_view["machine_count"] for account_view in account_views
        ),
        "token_totals": aggregate_token_fields(combined_model_usage),
        "memory_recall_savings": combined_savings,
        "first_session_date": _earliest(
            [account_view["first_session_date"] for account_view in account_views]
        ),
        "last_computed_date": _latest(
            [account_view["last_computed_date"] for account_view in account_views]
        ),
    }


def build_usage_view_model(snapshot_directory: Path) -> dict:
    account_views = group_snapshots_by_account(read_usage_snapshots(snapshot_directory))
    return {
        "accounts": account_views,
        "summary": summarize_accounts(account_views),
        "chart": build_chart_series(account_views),
    }
