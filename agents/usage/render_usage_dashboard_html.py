from __future__ import annotations

import json

from render_usage_dashboard_sections import (
    render_account_rows,
    render_chart_datasets,
    render_otel_panel,
    render_stat_cards,
)

NAVIGATION = (
    '<nav class="top">'
    '<a class="brand" href="../">dotfiles reports</a>'
    '<a href="../baseline/">baseline</a>'
    '<a href="../quality/">quality</a>'
    '<a href="../coverage/">coverage</a>'
    '<a href="../usage/" class="active">usage</a>'
    "</nav>"
)


def render_dashboard_html(view_model: dict) -> str:
    summary = view_model["summary"]
    stat_cards = render_stat_cards(summary) if summary["account_count"] else ""
    account_rows = render_account_rows(view_model["accounts"])
    otel_panel = render_otel_panel(summary.get("otel_metrics", {}))
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

<h2>OpenTelemetry token stream</h2>
<p class="lede">A local OpenTelemetry collector on every machine receives Claude Code's
<code>claude_code.token.usage</code> metric and writes it to a rotating local file. Each
machine folds the aggregated counts (never the account id) into its snapshot, so this is a
live, type-resolved view that corroborates the cache-read story above.</p>
{otel_panel}

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
