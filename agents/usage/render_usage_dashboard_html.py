from __future__ import annotations

import json

NAVIGATION = (
    '<nav class="top">'
    '<a class="brand" href="../">dotfiles reports</a>'
    '<a href="../baseline/">baseline</a>'
    '<a href="../quality/">quality</a>'
    '<a href="../coverage/">coverage</a>'
    '<a href="../usage/" class="active">usage</a>'
    "</nav>"
)

ACCOUNT_SERIES_COLORS = ["#58a6ff", "#3fb950", "#d29922", "#bc8cff", "#f85149"]


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


def render_dashboard_html(view_model: dict) -> str:
    summary = view_model["summary"]
    stat_cards = render_stat_cards(summary) if summary["account_count"] else ""
    account_rows = render_account_rows(view_model["accounts"])
    chart_labels = json.dumps(view_model["chart"]["dates"])
    chart_datasets = render_chart_datasets(view_model["chart"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>token usage across accounts | dotfiles</title>
<link rel="stylesheet" href="../style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>
{NAVIGATION}
<div class="wrap">
<h1>token usage across accounts</h1>
<p class="lede">Claude Code token consumption per account, pulled from each machine's
<code>stats-cache.json</code>. Every account is an opaque salted hash of its id, so the
numbers are public but the accounts are not. The headline number is cache-read tokens:
on a prompt-cached model they dwarf fresh input and are what actually burns the plan.</p>

<div class="cards">
{stat_cards}
</div>

<div class="chart-wrap"><canvas id="dailyTokensChart"></canvas></div>

<h2>Where the tokens go</h2>
<div class="panel">
<p>Claude Code reuses a cached prefix across turns, so almost every token a long session
reads is a <b>cache-read</b>, not fresh input. That is why the lever that matters is
cutting repeated context, not trimming prompts: the cache-read column below is the cost.</p>
</div>

<h2>Per-account totals</h2>
<table>
<thead><tr><th>account</th><th>machines</th><th>window</th><th>cache-read</th>
<th>output</th><th>cost (notional)</th><th>recalls suppressed</th></tr></thead>
<tbody>
{account_rows}
</tbody>
</table>

<h2>The memory-recall lever</h2>
<p class="lede">The memory-recall hook injects relevant memory files into a turn, then
suppresses the injection when the same set was already shown (dedup), when a per-session
budget is spent, or when nothing changed (debounce). Those suppressions are the directly
attributable savings folded into each snapshot.</p>

<h2>Honest caveat on attribution</h2>
<div class="panel">
<p>A machine carries one current account, and <code>stats-cache.json</code> is not split
by account. A machine that switched accounts attributes its whole local history to the
account active now, so the early part of a series can be pre-switch usage. Read the recent
slope as the current account's, not the absolute history.</p>
</div>

<footer>
Auto-generated from <code>agents/usage/snapshots/*.json</code> by
<code>agents/usage/render_usage_dashboard.py</code> on every push. Snapshots are exported
locally per machine by <code>agents/usage/export_usage_snapshot.py</code> because CI has no
<code>~/.claude</code> &middot;
<a href="../baseline/">agent-eval baseline</a>
</footer>
</div>

<script>
new Chart(document.getElementById("dailyTokensChart"), {{
  type: "line",
  data: {{ labels: {chart_labels}, datasets: {chart_datasets} }},
  options: {{
    plugins: {{
      legend: {{ labels: {{ color: "#e6edf3" }} }},
      title: {{ display: true, text: "daily tokens per account", color: "#8b949e" }}
    }},
    scales: {{
      y: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }},
      x: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""
