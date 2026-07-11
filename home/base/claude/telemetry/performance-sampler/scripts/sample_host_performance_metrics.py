import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ai_fleet_metrics
import browser_metrics
import input_layer_metrics
import multiplexer_metrics
import spotlight_metrics
import system_health_metrics
import terminal_metrics
from performance_log_archiver import archive_tmp_logs, should_archive_today
from performance_metrics_writer import (
    append_metric_records,
    current_month_performance_metrics_log_path,
    default_performance_metrics_state_directory,
    prune_performance_metrics_logs_older_than,
)

RETAINED_MONTHS = 6

METRIC_COLLECTOR_MODULES = [
    system_health_metrics,
    ai_fleet_metrics,
    browser_metrics,
    multiplexer_metrics,
    terminal_metrics,
    input_layer_metrics,
    spotlight_metrics,
]


def collect_all_metric_records() -> list:
    all_metric_records = []
    for collector_module in METRIC_COLLECTOR_MODULES:
        for collector_name, metric_collector in collector_module.metric_collectors:
            try:
                all_metric_records.extend(metric_collector())
            except Exception as collector_error:
                all_metric_records.append(
                    {
                        "metric": "collector_error",
                        "value": 1,
                        "labels": {
                            "collector": collector_name,
                            "error": str(collector_error),
                        },
                    }
                )
    return all_metric_records


def main() -> None:
    sample_timestamp = datetime.now(timezone.utc)
    hostname = os.environ.get("PERFORMANCE_SAMPLER_HOST") or socket.gethostname()
    state_directory = default_performance_metrics_state_directory()

    metric_records = collect_all_metric_records()
    log_path = current_month_performance_metrics_log_path(
        state_directory, sample_timestamp
    )
    append_metric_records(metric_records, log_path, sample_timestamp, hostname)
    prune_performance_metrics_logs_older_than(
        state_directory, sample_timestamp, RETAINED_MONTHS
    )

    today_iso_date = sample_timestamp.strftime("%Y-%m-%d")
    if should_archive_today(state_directory, today_iso_date):
        archive_tmp_logs(state_directory, sample_timestamp, RETAINED_MONTHS)


if __name__ == "__main__":
    main()
