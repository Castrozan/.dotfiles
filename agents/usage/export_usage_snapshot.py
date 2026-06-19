from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from current_usage_snapshot import build_current_usage_snapshot  # noqa: E402
from usage_snapshot_writer import write_usage_snapshot  # noqa: E402

DEFAULT_SNAPSHOT_DIRECTORY = Path(__file__).resolve().parent / "snapshots"


def main() -> int:
    usage_snapshot = build_current_usage_snapshot()
    if usage_snapshot is None:
        print(
            "no current Claude account in ~/.claude.json; nothing exported",
            file=sys.stderr,
        )
        return 1
    snapshot_path = write_usage_snapshot(DEFAULT_SNAPSHOT_DIRECTORY, usage_snapshot)
    print(f"wrote {snapshot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
