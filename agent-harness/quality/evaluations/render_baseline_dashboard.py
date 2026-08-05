import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_baseline_dashboard_data import (  # noqa: E402
    collect_baseline_revisions,
    summarize_revisions,
)
from render_baseline_dashboard_html import render_dashboard_html  # noqa: E402


def main():
    output_directory = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    output_directory.mkdir(parents=True, exist_ok=True)
    revisions = collect_baseline_revisions()
    summary = summarize_revisions(revisions)
    latest_baseline_age_days = (
        (date.today() - date.fromisoformat(summary["last_date"])).days
        if summary
        else None
    )
    (output_directory / "index.html").write_text(
        render_dashboard_html(revisions, summary, latest_baseline_age_days)
    )
    print(f"wrote {output_directory / 'index.html'} with {len(revisions)} revisions")


if __name__ == "__main__":
    main()
