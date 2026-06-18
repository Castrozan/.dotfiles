from __future__ import annotations

import json
from pathlib import Path

USAGE_SNAPSHOT_SCHEMA_VERSION = 1


def build_usage_snapshot(
    account_label: str,
    machine_label: str,
    stats_cache_summary: dict,
    memory_recall_savings: dict,
    otel_metrics: dict,
) -> dict:
    return {
        "schema_version": USAGE_SNAPSHOT_SCHEMA_VERSION,
        "account_label": account_label,
        "machine_label": machine_label,
        **stats_cache_summary,
        "memory_recall_savings": memory_recall_savings,
        "otel_metrics": otel_metrics,
    }


def usage_snapshot_file_name(account_label: str, machine_label: str) -> str:
    return f"{account_label}-{machine_label}.json"


def write_usage_snapshot(snapshot_directory: Path, usage_snapshot: dict) -> Path:
    snapshot_directory.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_directory / usage_snapshot_file_name(
        usage_snapshot["account_label"], usage_snapshot["machine_label"]
    )
    snapshot_path.write_text(
        json.dumps(usage_snapshot, indent=2, sort_keys=True) + "\n"
    )
    return snapshot_path
