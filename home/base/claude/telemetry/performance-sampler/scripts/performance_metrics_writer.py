import json
from pathlib import Path


def default_performance_metrics_state_directory() -> Path:
    return Path.home() / ".local" / "state" / "performance-metrics"


def current_month_performance_metrics_log_path(
    state_directory: Path, sample_timestamp
) -> Path:
    return state_directory / f"performance-{sample_timestamp:%Y-%m}.jsonl"


def format_metric_record_line(record: dict, sample_timestamp, hostname: str) -> str:
    line_object = {
        "timestamp": sample_timestamp.isoformat(),
        "host": hostname,
        "metric": record["metric"],
        "value": record["value"],
        "labels": record.get("labels", {}),
    }
    return json.dumps(line_object, separators=(",", ":"), sort_keys=True)


def append_metric_records(
    records, log_path: Path, sample_timestamp, hostname: str
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatted_lines = [
        format_metric_record_line(record, sample_timestamp, hostname)
        for record in records
    ]
    with log_path.open("a", encoding="utf-8") as log_file:
        for formatted_line in formatted_lines:
            log_file.write(formatted_line + "\n")


def parse_month_key_from_log_name(log_file_name: str):
    month_stem = log_file_name.removeprefix("performance-").removesuffix(".jsonl")
    stem_parts = month_stem.split("-")
    if len(stem_parts) != 2:
        return None
    try:
        year = int(stem_parts[0])
        month = int(stem_parts[1])
    except ValueError:
        return None
    if not 1 <= month <= 12:
        return None
    return year * 12 + (month - 1)


def prune_performance_metrics_logs_older_than(
    state_directory: Path, sample_timestamp, retained_months: int
) -> list:
    if not state_directory.is_dir():
        return []
    current_month_key = sample_timestamp.year * 12 + (sample_timestamp.month - 1)
    oldest_retained_month_key = current_month_key - (retained_months - 1)
    removed_log_paths = []
    for candidate_log_path in state_directory.glob("performance-*.jsonl"):
        candidate_month_key = parse_month_key_from_log_name(candidate_log_path.name)
        if candidate_month_key is None:
            continue
        if candidate_month_key < oldest_retained_month_key:
            candidate_log_path.unlink()
            removed_log_paths.append(candidate_log_path)
    return removed_log_paths
