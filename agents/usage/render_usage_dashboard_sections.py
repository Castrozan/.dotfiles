from __future__ import annotations

import json

ACCOUNT_SERIES_COLORS = ["#58a6ff", "#3fb950", "#d29922", "#bc8cff", "#f85149"]
OTEL_TOKEN_TYPE_LABELS = {
    "cacheRead": "cache read",
    "cacheCreation": "cache creation",
    "input": "input",
    "output": "output",
}
OTEL_TOKEN_TYPE_ORDER = ("cacheRead", "cacheCreation", "input", "output")


def format_token_count(token_count: float) -> str:
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if token_count >= divisor:
            return f"{token_count / divisor:.2f}{suffix}"
    return str(int(token_count))


def cache_read_share_percent(token_totals: dict) -> float:
    cache_read = token_totals.get("cache_read_input_tokens", 0)
    cache_creation = token_totals.get("cache_creation_input_tokens", 0)
    fresh_input = token_totals.get("input_tokens", 0)
    input_side_total = cache_read + cache_creation + fresh_input
    if input_side_total == 0:
        return 0.0
    return round(cache_read / input_side_total * 100, 1)


def render_stat_cards(summary: dict) -> str:
    token_totals = summary["token_totals"]
    savings = summary["memory_recall_savings"]
    cards = [
        (
            "accounts tracked",
            str(summary["account_count"]),
            f"across {summary['machine_count']} machine(s)",
        ),
        (
            "cache-read tokens",
            format_token_count(token_totals["cache_read_input_tokens"]),
            "the dominant cost driver",
        ),
        (
            "cache-read share",
            f"{cache_read_share_percent(token_totals)}%",
            "of all input-side tokens",
        ),
        (
            "recall events suppressed",
            str(savings["suppressed_recall_event_total"]),
            "budget + debounce + dedup",
        ),
        (
            "dedup chars saved",
            format_token_count(savings["dedup_suppressed_character_total"]),
            "duplicate recalls stopped",
        ),
    ]
    return "\n".join(
        f'<div class="card"><div class="k">{value}</div>'
        f'<div class="l">{label}</div><div class="s">{sub}</div></div>'
        for label, value, sub in cards
    )


def render_account_rows(account_views: list[dict]) -> str:
    rows = []
    for account_view in account_views:
        token_totals = account_view["token_totals"]
        savings = account_view["memory_recall_savings"]
        rows.append(
            "<tr>"
            f"<td><code>{account_view['account_label']}</code></td>"
            f"<td>{account_view['machine_count']}</td>"
            f"<td>{account_view['first_session_date'] or '-'} to "
            f"{account_view['last_computed_date'] or '-'}</td>"
            f"<td>{format_token_count(token_totals['cache_read_input_tokens'])}</td>"
            f"<td>{format_token_count(token_totals['output_tokens'])}</td>"
            f"<td>${token_totals['cost_usd']:,.0f}</td>"
            f"<td>{savings['suppressed_recall_event_total']}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_chart_datasets(chart: dict) -> str:
    datasets = []
    for series_index, account_series in enumerate(chart["series"]):
        color = ACCOUNT_SERIES_COLORS[series_index % len(ACCOUNT_SERIES_COLORS)]
        datasets.append(
            {
                "label": account_series["account_label"],
                "data": account_series["values"],
                "borderColor": color,
                "backgroundColor": color + "26",
                "tension": 0.2,
                "spanGaps": True,
                "pointRadius": 2,
            }
        )
    return json.dumps(datasets)


def _ordered_otel_token_types(token_usage_by_type: dict) -> list[str]:
    known = [t for t in OTEL_TOKEN_TYPE_ORDER if t in token_usage_by_type]
    extra = [t for t in token_usage_by_type if t not in OTEL_TOKEN_TYPE_ORDER]
    return known + sorted(extra)


def render_otel_panel(otel_metrics: dict) -> str:
    if not otel_metrics.get("has_data"):
        return (
            '<div class="panel"><p>The local OpenTelemetry collector runs on every machine, '
            "but no metrics interval has been flushed yet. Real-time token counts by type "
            "appear here once Claude Code exports its first batch.</p></div>"
        )
    token_usage_by_type = otel_metrics["token_usage_by_type"]
    chips = "\n".join(
        f'<span class="chip">{OTEL_TOKEN_TYPE_LABELS.get(token_type, token_type)}: '
        f"{format_token_count(token_usage_by_type[token_type])}</span>"
        for token_type in _ordered_otel_token_types(token_usage_by_type)
    )
    total_cost_usd = otel_metrics.get("total_cost_usd", 0)
    return (
        f'<div class="chips">{chips}</div>'
        '<div class="panel"><p>Live token counts straight from Claude Code\'s '
        "OpenTelemetry stream, aggregated across machines and independent of the "
        f"stats-cache series above. Notional cost on the stream: <b>${total_cost_usd:,.2f}</b>."
        "</p></div>"
    )
