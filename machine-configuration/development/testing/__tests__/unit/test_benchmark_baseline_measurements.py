import json
from datetime import datetime, timezone

import benchmark_baseline

SAVE_COMMAND = "benchmark-rebuild --save-baseline"


def _document(**overrides) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": "abc1234",
        "host": "kira",
        "config": "darwin",
        "threshold_percent": 150,
        **overrides,
    }


def _failures(tmp_path, measurements) -> list[str]:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(_document(measurements=measurements)))
    return benchmark_baseline.validate_tracked_baseline(
        baseline_path, "duration_seconds", "max_allowed_seconds", SAVE_COMMAND
    ).failures


class TestMeasurementsField:
    def test_reports_a_non_object_measurements_field(self, tmp_path):
        assert _failures(tmp_path, ["eval"]) == [
            "Baseline measurements are not a JSON object."
        ]

    def test_reports_a_missing_measurements_field(self, tmp_path):
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(_document()))
        failures = benchmark_baseline.validate_tracked_baseline(
            baseline_path, "duration_seconds", "max_allowed_seconds", SAVE_COMMAND
        ).failures
        assert failures == ["Baseline measurements are not a JSON object."]

    def test_reports_an_empty_measurement_set(self, tmp_path):
        assert _failures(tmp_path, {}) == ["Baseline has no measurements."]

    def test_reports_a_non_object_measurement_entry(self, tmp_path):
        assert _failures(tmp_path, {"eval": 12.0}) == [
            "eval: measurement entry is not a JSON object"
        ]


class TestMeasurementValues:
    def test_accepts_positive_numbers(self, tmp_path):
        measurements = {"eval": {"duration_seconds": 2, "max_allowed_seconds": 3.5}}
        assert _failures(tmp_path, measurements) == []

    def test_reports_a_missing_measurement_value(self, tmp_path):
        measurements = {"eval": {"max_allowed_seconds": 3.0}}
        assert _failures(tmp_path, measurements) == ["eval: missing duration_seconds"]

    def test_reports_a_missing_ceiling(self, tmp_path):
        measurements = {"eval": {"duration_seconds": 2.0}}
        assert _failures(tmp_path, measurements) == [
            "eval: missing max_allowed_seconds"
        ]

    def test_reports_a_non_numeric_ceiling(self, tmp_path):
        measurements = {"eval": {"duration_seconds": 2.0, "max_allowed_seconds": "3"}}
        assert _failures(tmp_path, measurements) == [
            "eval: max_allowed_seconds is not a number"
        ]

    def test_reports_a_null_measurement_value(self, tmp_path):
        measurements = {"eval": {"duration_seconds": None, "max_allowed_seconds": 3.0}}
        assert _failures(tmp_path, measurements) == [
            "eval: duration_seconds is not a number"
        ]

    def test_reports_a_boolean_measurement_value(self, tmp_path):
        measurements = {"eval": {"duration_seconds": True, "max_allowed_seconds": 3.0}}
        assert _failures(tmp_path, measurements) == [
            "eval: duration_seconds is not a number"
        ]

    def test_reports_a_non_positive_ceiling(self, tmp_path):
        measurements = {"eval": {"duration_seconds": 2.0, "max_allowed_seconds": 0}}
        assert _failures(tmp_path, measurements) == [
            "eval: max_allowed_seconds must be greater than zero"
        ]

    def test_reports_a_negative_measurement_value(self, tmp_path):
        measurements = {"eval": {"duration_seconds": -1.0, "max_allowed_seconds": 3.0}}
        assert _failures(tmp_path, measurements) == [
            "eval: duration_seconds must be greater than zero"
        ]

    def test_reports_every_broken_component(self, tmp_path):
        measurements = {
            "eval": {"duration_seconds": 2.0, "max_allowed_seconds": 3.0},
            "rebuild": {"duration_seconds": 0},
        }
        assert _failures(tmp_path, measurements) == [
            "rebuild: duration_seconds must be greater than zero",
            "rebuild: missing max_allowed_seconds",
        ]


class TestDesktopMeasurementKeys:
    def test_validates_the_desktop_value_and_ceiling_keys(self, tmp_path):
        baseline_path = tmp_path / "baseline-desktop.json"
        baseline_path.write_text(
            json.dumps(
                _document(measurements={"comp": {"avg_ms": 0, "max_allowed_ms": 100}})
            )
        )
        failures = benchmark_baseline.validate_tracked_baseline(
            baseline_path, "avg_ms", "max_allowed_ms", "benchmark-desktop"
        ).failures
        assert failures == ["comp: avg_ms must be greater than zero"]
