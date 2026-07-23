import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY))

import performance_metrics_writer

SAMPLE_TIMESTAMP = datetime(2026, 7, 11, 19, 25, 31, tzinfo=timezone.utc)


def test_format_metric_record_line_round_trips_all_fields():
    record = {
        "metric": "memory_pressure_level",
        "value": 1,
        "labels": {"kind": "level"},
    }
    line = performance_metrics_writer.format_metric_record_line(
        record, SAMPLE_TIMESTAMP, "kira"
    )
    decoded = json.loads(line)
    assert decoded == {
        "timestamp": "2026-07-11T19:25:31+00:00",
        "host": "kira",
        "metric": "memory_pressure_level",
        "value": 1,
        "labels": {"kind": "level"},
    }


def test_current_month_performance_metrics_log_path_uses_year_month():
    log_path = performance_metrics_writer.current_month_performance_metrics_log_path(
        Path("/state"), SAMPLE_TIMESTAMP
    )
    assert log_path == Path("/state/performance-2026-07.jsonl")


def test_parse_month_key_from_log_name_parses_valid_and_rejects_invalid():
    parse = performance_metrics_writer.parse_month_key_from_log_name
    assert parse("performance-2026-07.jsonl") == 2026 * 12 + 6
    assert parse("performance-2026-13.jsonl") is None
    assert parse("performance-bad.jsonl") is None
    assert parse("unrelated.txt") is None


def test_append_metric_records_writes_one_json_line_per_record(tmp_path):
    log_path = tmp_path / "performance-2026-07.jsonl"
    records = [
        {"metric": "a", "value": 1, "labels": {}},
        {"metric": "b", "value": 2.5, "labels": {"x": "y"}},
    ]
    performance_metrics_writer.append_metric_records(
        records, log_path, SAMPLE_TIMESTAMP, "kira"
    )
    written_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(written_lines) == 2
    assert json.loads(written_lines[1])["metric"] == "b"
    assert json.loads(written_lines[1])["value"] == 2.5


def test_prune_performance_metrics_logs_older_than_keeps_recent_months(tmp_path):
    for month_stem in ("2026-07", "2026-06", "2026-02", "2025-12"):
        (tmp_path / f"performance-{month_stem}.jsonl").write_text(
            "{}\n", encoding="utf-8"
        )
    (tmp_path / "unrelated.txt").write_text("keep", encoding="utf-8")

    removed = performance_metrics_writer.prune_performance_metrics_logs_older_than(
        tmp_path, SAMPLE_TIMESTAMP, retained_months=6
    )

    surviving_names = {path.name for path in tmp_path.glob("performance-*.jsonl")}
    assert surviving_names == {
        "performance-2026-07.jsonl",
        "performance-2026-06.jsonl",
        "performance-2026-02.jsonl",
    }
    assert {path.name for path in removed} == {"performance-2025-12.jsonl"}
    assert (tmp_path / "unrelated.txt").exists()
