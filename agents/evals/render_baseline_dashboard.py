import json
import subprocess
import sys
from pathlib import Path

BASELINE_REPOSITORY_PATH = "agents/evals/baseline.json"
RESET_PLACEHOLDER_TOTAL_TESTS = 1


def commits_touching_baseline():
    output = (
        subprocess.run(
            [
                "git",
                "log",
                "--reverse",
                "--format=%H|%cI",
                "--",
                BASELINE_REPOSITORY_PATH,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
        .splitlines()
    )
    for line in output:
        commit_sha, committed_iso = line.split("|", 1)
        yield commit_sha, committed_iso


def baseline_at_commit(commit_sha):
    blob = subprocess.run(
        ["git", "show", f"{commit_sha}:{BASELINE_REPOSITORY_PATH}"],
        capture_output=True,
        text=True,
    ).stdout
    if not blob.strip():
        return None
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def collect_baseline_revisions():
    revisions = []
    for commit_sha, committed_iso in commits_touching_baseline():
        baseline = baseline_at_commit(commit_sha)
        if baseline is None:
            continue
        total_tests = baseline.get("total_tests")
        if total_tests == RESET_PLACEHOLDER_TOTAL_TESTS:
            continue
        rate = baseline.get("pass_rate")
        revisions.append(
            {
                "date": committed_iso[:10],
                "commit": commit_sha[:8],
                "passed": baseline.get("total_passed"),
                "total": total_tests,
                "rate": round(rate * 100, 1)
                if isinstance(rate, (int, float))
                else None,
            }
        )
    return revisions


def render_dashboard_html(revisions):
    data_json = json.dumps(revisions)
    latest = revisions[-1] if revisions else None
    latest_summary = (
        f"{latest['rate']}% &middot; {latest['passed']}/{latest['total']} &middot; {latest['date']}"
        if latest
        else "no data"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dotfiles agent-eval baseline</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {{ color-scheme: dark; }}
  body {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; margin: 0; padding: 2rem;
         background: #0d1117; color: #e6edf3; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 .25rem; }}
  .subtitle {{ color: #8b949e; margin: 0 0 1.5rem; }}
  .latest {{ font-size: 1.1rem; margin: 0 0 1.5rem; color: #58a6ff; }}
  .chart-wrap {{ max-width: 960px; background: #161b22; border: 1px solid #30363d;
                border-radius: 8px; padding: 1rem; margin-bottom: 2rem; }}
  table {{ border-collapse: collapse; font-size: .85rem; }}
  th, td {{ text-align: left; padding: .3rem .8rem; border-bottom: 1px solid #21262d; }}
  th {{ color: #8b949e; }}
  a {{ color: #58a6ff; }}
</style>
</head>
<body>
<h1>dotfiles agent-eval baseline</h1>
<p class="subtitle">Tier-1 static-eval pass rate over time, read from the git history of
<code>agents/evals/baseline.json</code>. Rebuilt automatically on every push.</p>
<p class="latest">latest: {latest_summary}</p>
<div class="chart-wrap"><canvas id="passRateChart"></canvas></div>
<table id="dataTable">
<thead><tr><th>date</th><th>commit</th><th>passed</th><th>total</th><th>pass rate</th></tr></thead>
<tbody></tbody>
</table>
<script>
const revisions = {data_json};
const labels = revisions.map(r => r.date);
const rates = revisions.map(r => r.rate);
new Chart(document.getElementById("passRateChart"), {{
  type: "line",
  data: {{ labels, datasets: [{{
    label: "pass rate %", data: rates, borderColor: "#58a6ff",
    backgroundColor: "rgba(88,166,255,.15)", fill: true, tension: .2,
    pointRadius: 3, pointHoverRadius: 5
  }}] }},
  options: {{
    scales: {{ y: {{ suggestedMin: 80, suggestedMax: 100,
      ticks: {{ color: "#8b949e", callback: v => v + "%" }}, grid: {{ color: "#21262d" }} }},
      x: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }} }},
    plugins: {{ legend: {{ labels: {{ color: "#e6edf3" }} }} }}
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


def main():
    output_directory = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    output_directory.mkdir(parents=True, exist_ok=True)
    revisions = collect_baseline_revisions()
    (output_directory / "index.html").write_text(render_dashboard_html(revisions))
    print(f"wrote {output_directory / 'index.html'} with {len(revisions)} revisions")


if __name__ == "__main__":
    main()
