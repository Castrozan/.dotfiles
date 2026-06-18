from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from account_label_anonymizer import (  # noqa: E402
    default_claude_account_config_path,
    derive_account_label,
    derive_machine_label,
    read_current_account_uuid,
)
from claude_usage_stats_reader import (  # noqa: E402
    default_stats_cache_path,
    read_stats_cache,
    summarize_stats_cache,
)
from memory_recall_savings_reader import (  # noqa: E402
    summarize_memory_recall_savings_in_directory,
)
from usage_snapshot_writer import build_usage_snapshot, write_usage_snapshot  # noqa: E402

DEFAULT_SNAPSHOT_DIRECTORY = Path(__file__).resolve().parent / "snapshots"
DEFAULT_MEMORY_RECALL_STATE_DIRECTORY = Path("/tmp")


def memory_recall_state_directory() -> Path:
    override = os.environ.get("MEMORY_RECALL_DEBOUNCE_STATE_DIRECTORY")
    return Path(override) if override else DEFAULT_MEMORY_RECALL_STATE_DIRECTORY


def main() -> int:
    account_uuid = read_current_account_uuid(default_claude_account_config_path())
    if account_uuid is None:
        print(
            "no current Claude account in ~/.claude.json; nothing exported",
            file=sys.stderr,
        )
        return 1
    account_label = derive_account_label(account_uuid)
    machine_label = derive_machine_label(socket.gethostname())
    stats_cache_summary = summarize_stats_cache(
        read_stats_cache(default_stats_cache_path())
    )
    memory_recall_savings = summarize_memory_recall_savings_in_directory(
        memory_recall_state_directory()
    )
    usage_snapshot = build_usage_snapshot(
        account_label, machine_label, stats_cache_summary, memory_recall_savings
    )
    snapshot_path = write_usage_snapshot(DEFAULT_SNAPSHOT_DIRECTORY, usage_snapshot)
    print(f"wrote {snapshot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
