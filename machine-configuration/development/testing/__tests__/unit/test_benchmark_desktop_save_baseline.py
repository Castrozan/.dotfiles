import json
from unittest.mock import patch

import pytest

import benchmark_desktop


def _result(name, average_ms, errored):
    return {
        "name": name,
        "avg": average_ms,
        "min": average_ms,
        "max": average_ms,
        "times": [] if errored else [average_ms],
        "error": errored,
    }


class TestSaveBaseline:
    def _save(self, baseline_file, results) -> bool:
        with (
            patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file),
            patch(
                "benchmark_desktop.get_current_git_short_commit",
                return_value="abc",
            ),
        ):
            return benchmark_desktop.save_baseline(results)

    def test_writes_baseline_file(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        assert self._save(baseline_file, [_result("test", 50.0, False)]) is True

        data = json.loads(baseline_file.read_text())
        assert data["measurements"]["test"]["avg_ms"] == 50.0
        assert data["measurements"]["test"]["max_allowed_ms"] == 100.0

    def test_saves_only_the_successful_measurements(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        results = [_result("ok", 50.0, False), _result("bad", 0, True)]
        assert self._save(baseline_file, results) is True

        data = json.loads(baseline_file.read_text())
        assert "ok" in data["measurements"]
        assert "bad" not in data["measurements"]

    def test_refuses_to_create_a_baseline_when_every_measurement_failed(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        results = [_result("a", 0, True), _result("b", 0, True)]

        assert self._save(baseline_file, results) is False
        assert not baseline_file.exists()

    def test_leaves_an_existing_baseline_untouched_when_every_measurement_failed(
        self, tmp_path
    ):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text('{"kept": true}\n')

        assert self._save(baseline_file, [_result("a", 0, True)]) is False
        assert baseline_file.read_text() == '{"kept": true}\n'

    def test_refuses_when_no_component_was_measured_at_all(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        assert self._save(baseline_file, []) is False
        assert not baseline_file.exists()


class TestSaveBaselineExitStatus:
    def test_exits_non_zero_when_every_measurement_failed(self, tmp_path):
        results_file = tmp_path / "results.csv"

        with (
            patch("benchmark_desktop.sys.argv", ["cmd", "--save-baseline"]),
            patch(
                "benchmark_desktop.get_results_file_path",
                return_value=results_file,
            ),
            patch("benchmark_desktop.ensure_results_file_exists"),
            patch(
                "benchmark_desktop.get_available_benchmarks",
                return_value=[("broken", lambda: None)],
            ),
            patch(
                "benchmark_desktop.run_benchmarks",
                return_value=[_result("broken", 0, True)],
            ),
            patch("benchmark_desktop.save_baseline", return_value=False),
        ):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_desktop.main()
            assert exit_info.value.code == 1

    def test_exits_zero_when_a_measurement_succeeded(self, tmp_path):
        results_file = tmp_path / "results.csv"

        with (
            patch("benchmark_desktop.sys.argv", ["cmd", "--save-baseline"]),
            patch(
                "benchmark_desktop.get_results_file_path",
                return_value=results_file,
            ),
            patch("benchmark_desktop.ensure_results_file_exists"),
            patch(
                "benchmark_desktop.get_available_benchmarks",
                return_value=[("working", lambda: None)],
            ),
            patch(
                "benchmark_desktop.run_benchmarks",
                return_value=[_result("working", 50.0, False)],
            ),
            patch("benchmark_desktop.save_baseline", return_value=True),
        ):
            benchmark_desktop.main()
