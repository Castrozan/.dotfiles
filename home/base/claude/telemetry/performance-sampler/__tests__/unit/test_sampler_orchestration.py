import sys
import types
from pathlib import Path

PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY))

import sample_host_performance_metrics


def test_collect_all_metric_records_isolates_failing_collector(monkeypatch):
    def healthy_collector():
        return [{"metric": "ok_metric", "value": 3, "labels": {}}]

    def failing_collector():
        raise RuntimeError("probe exploded")

    stub_module = types.SimpleNamespace(
        metric_collectors=[
            ("stub.healthy", healthy_collector),
            ("stub.failing", failing_collector),
        ]
    )
    monkeypatch.setattr(
        sample_host_performance_metrics, "METRIC_COLLECTOR_MODULES", [stub_module]
    )

    records = sample_host_performance_metrics.collect_all_metric_records()

    healthy_records = [record for record in records if record["metric"] == "ok_metric"]
    error_records = [
        record for record in records if record["metric"] == "collector_error"
    ]
    assert len(healthy_records) == 1
    assert len(error_records) == 1
    assert error_records[0]["value"] == 1
    assert error_records[0]["labels"]["collector"] == "stub.failing"
    assert "probe exploded" in error_records[0]["labels"]["error"]
