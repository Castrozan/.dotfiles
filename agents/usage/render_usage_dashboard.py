from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_usage_dashboard_data import (  # noqa: E402
    DEFAULT_SNAPSHOT_DIRECTORY,
    build_usage_view_model,
)
from render_usage_dashboard_html import render_dashboard_html  # noqa: E402


def main() -> None:
    output_directory = Path(sys.argv[1] if len(sys.argv) > 1 else "site/usage")
    output_directory.mkdir(parents=True, exist_ok=True)
    view_model = build_usage_view_model(DEFAULT_SNAPSHOT_DIRECTORY)
    (output_directory / "index.html").write_text(render_dashboard_html(view_model))
    print(
        f"wrote {output_directory / 'index.html'} with "
        f"{view_model['summary']['account_count']} account(s)"
    )


if __name__ == "__main__":
    main()
