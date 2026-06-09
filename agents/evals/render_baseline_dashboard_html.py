import json

NAVIGATION = (
    '<nav class="top">'
    '<a class="brand" href="../">dotfiles reports</a>'
    '<a href="../baseline/" class="active">baseline</a>'
    '<a href="../quality/">quality</a>'
    '<a href="../coverage/">coverage</a>'
    "</nav>"
)


def render_stat_cards(summary):
    latest = summary["latest"]
    peak = summary["peak"]
    trough = summary["trough"]
    suite = (
        str(summary["suite_min"])
        if summary["suite_min"] == summary["suite_max"]
        else f"{summary['suite_min']}-{summary['suite_max']}"
    )
    cards = [
        (
            "current pass rate",
            f"{latest['rate']}%",
            f"{latest['passed']}/{latest['total']} on {latest['date']}",
        ),
        ("all-time high", f"{peak['rate']}%", f"{peak['date']} ({peak['commit']})"),
        (
            "all-time low",
            f"{trough['rate']}%",
            f"{trough['date']} ({trough['commit']})",
        ),
        (
            "baselines recorded",
            str(summary["count"]),
            f"{summary['first_date']} to {summary['last_date']}",
        ),
        ("suite size", suite, "tests per run"),
    ]
    return "\n".join(
        f'<div class="card"><div class="k">{value}</div>'
        f'<div class="l">{label}</div><div class="s">{sub}</div></div>'
        for label, value, sub in cards
    )


def render_dashboard_html(revisions, summary):
    data_json = json.dumps(revisions)
    stat_cards = render_stat_cards(summary) if summary else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agent-eval baseline | dotfiles</title>
<link rel="stylesheet" href="../style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>
{NAVIGATION}
<div class="wrap">
<h1>agent-eval baseline</h1>
<p class="lede">How well the AI agent on this machine obeys the dotfiles instruction surface,
tracked over time. Each point is one recorded eval run; the line is the share of compliance tests
the agent passed against the instructions as they stood at that commit.</p>

<div class="cards">
{stat_cards}
</div>

<div class="chart-wrap"><canvas id="passRateChart"></canvas></div>

<h2>What this measures</h2>
<div class="panel">
<p>This is the <b>Tier-1 static-eval pass rate</b> - the headline health number for the agent's
instruction compliance. A suite of prompt-based evals in <code>agents/evals/</code> runs each prompt
through <code>claude -p</code> (Claude Max, haiku, no API cost) inside a throwaway git worktree,
then checks assertions on the answer. Tests are bucketed into <code>compliance</code>,
<code>routing</code>, <code>navigation</code>, <code>knowledge</code> and <code>other</code>.</p>
<p>Running <code>agent-eval --save-baseline</code> executes the whole suite and commits the result
to <code>agents/evals/baseline.json</code>. This page reads that file's full git history, so every
point is a commit - the chart is the repo remembering its own report cards.</p>
</div>

<h2>The gate that keeps it honest</h2>
<p class="lede"><code>agent-eval --check-baseline</code> runs in CI with
no model calls. It just reads the committed baseline and fails the build when:</p>
<div class="chips">
<span class="chip">overall pass rate <b>&ge; 75%</b></span>
<span class="chip">compliance pass rate <b>&ge; 85%</b></span>
</div>
<p class="lede">The baseline is a committed snapshot, refreshed intentionally with
<code>agent-eval --save-baseline</code> when the instruction surface meaningfully changes - never on a
clock. CI only guards the absolute floor, so this number moves only when someone records a new run.
Dips that do not reproduce on a standalone re-run are concurrency noise on long runs, not real
regressions.</p>

<h2>Every recorded baseline</h2>
<table id="dataTable">
<thead><tr><th>date</th><th>commit</th><th>passed</th><th>total</th><th>pass rate</th></tr></thead>
<tbody></tbody>
</table>

<footer>
Auto-generated from <code>agents/evals/baseline.json</code> history by
<code>agents/evals/render_baseline_dashboard.py</code> on every push &middot;
<a href="../quality/">how quality is measured</a> &middot;
<a href="https://github.com/Castrozan/.dotfiles/issues/70">design notes</a>
</footer>
</div>

<script>
const revisions = {data_json};
const labels = revisions.map(r => r.date);
const rates = revisions.map(r => r.rate);
new Chart(document.getElementById("passRateChart"), {{
  type: "line",
  data: {{ labels, datasets: [{{
    label: "pass rate %", data: rates, borderColor: "#58a6ff",
    backgroundColor: "rgba(88,166,255,.15)", fill: true, tension: .2,
    pointRadius: 3, pointHoverRadius: 6, pointBackgroundColor: "#58a6ff"
  }}] }},
  options: {{
    plugins: {{
      legend: {{ labels: {{ color: "#e6edf3" }} }},
      tooltip: {{ callbacks: {{
        label: (ctx) => {{
          const r = revisions[ctx.dataIndex];
          return ` ${{r.rate}}%  (${{r.passed}}/${{r.total}})  ${{r.commit}}`;
        }}
      }} }}
    }},
    scales: {{
      y: {{ suggestedMin: 80, suggestedMax: 100,
        ticks: {{ color: "#8b949e", callback: v => v + "%" }}, grid: {{ color: "#21262d" }} }},
      x: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }}
    }}
  }}
}});
const tbody = document.querySelector("#dataTable tbody");
for (const r of revisions) {{
  const tr = document.createElement("tr");
  tr.innerHTML = `<td>${{r.date}}</td><td>${{r.commit}}</td><td>${{r.passed}}</td>` +
                 `<td>${{r.total}}</td><td>${{r.rate}}%</td>`;
  tbody.appendChild(tr);
}}
</script>
</body>
</html>
"""
