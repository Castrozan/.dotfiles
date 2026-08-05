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
from claude_otel_metrics_reader import (  # noqa: E402
    default_otel_metrics_file_path,
    summarize_otel_metrics_file,
)
from claude_usage_stats_reader import (  # noqa: E402
    default_stats_cache_path,
    read_stats_cache,
    summarize_stats_cache,
)
from usage_snapshot_writer import build_usage_snapshot  # noqa: E402


def build_current_usage_snapshot() -> dict | None:
    account_uuid = read_current_account_uuid(default_claude_account_config_path())
    if account_uuid is None:
        return None
    account_label = derive_account_label(account_uuid)
    machine_label = derive_machine_label(socket.gethostname())
    stats_cache_summary = summarize_stats_cache(
        read_stats_cache(default_stats_cache_path())
    )
    otel_metrics = summarize_otel_metrics_file(default_otel_metrics_file_path())
    return build_usage_snapshot(
        account_label,
        machine_label,
        stats_cache_summary,
        otel_metrics,
    )
