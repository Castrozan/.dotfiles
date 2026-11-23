import json
from unittest.mock import patch

import benchmark_desktop
import desktop_benchmarks.baseline
import desktop_benchmarks.catalog
import desktop_benchmarks.results
import pytest
from benchmark_core import BenchmarkTarget

CHISE = BenchmarkTarget(
    "chise", "nixos", "nixosConfigurations.chise.config.system.build.toplevel"
)


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
            patch.object(desktop_benchmarks.baseline, "BASELINE_PATH", baseline_file),
            patch(
                "benchmark_core.get_current_git_short_commit",
                return_value="abc",
            ),
            patch(
                "benchmark_core.required_benchmark_target",
                return_value=CHISE,
            ),
        ):
            return desktop_benchmarks.baseline.save_baseline(results)

    def test_writes_baseline_file(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        assert self._save(baseline_file, [_result("test", 50.0, False)]) is True

        data = json.loads(baseline_file.read_text())
        assert data["measurements"]["test"]["avg_ms"] == 50.0
        assert data["measurements"]["test"]["max_allowed_ms"] == 100.0

    def test_leaves_an_existing_baseline_untouched_when_every_measurement_failed(
        self, tmp_path
    ):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text('{"kept": true}\n')

        assert self._save(baseline_file, [_result("a", 0, True)]) is False
        assert baseline_file.read_text() == '{"kept": true}\n'


class TestSaveBaselineExitStatus:
    def test_exits_non_zero_when_every_measurement_failed(self, tmp_path):
        results_file = tmp_path / "results.csv"

        with (
            patch("sys.argv", ["cmd", "--save-baseline"]),
            patch(
                "desktop_benchmarks.results.get_results_file_path",
                return_value=results_file,
            ),
            patch("benchmark_core.ensure_results_file_exists"),
            patch(
                "desktop_benchmarks.catalog.get_available_benchmarks",
                return_value=[("broken", lambda: None)],
            ),
            patch(
                "desktop_benchmarks.results.run_benchmarks",
                return_value=[_result("broken", 0, True)],
            ),
            patch("desktop_benchmarks.baseline.save_baseline", return_value=False),
        ):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_desktop.main()
            assert exit_info.value.code == 1

    def test_exits_zero_when_a_measurement_succeeded(self, tmp_path):
        results_file = tmp_path / "results.csv"

        with (
            patch("sys.argv", ["cmd", "--save-baseline"]),
            patch(
                "desktop_benchmarks.results.get_results_file_path",
                return_value=results_file,
            ),
            patch("benchmark_core.ensure_results_file_exists"),
            patch(
                "desktop_benchmarks.catalog.get_available_benchmarks",
                return_value=[("working", lambda: None)],
            ),
            patch(
                "desktop_benchmarks.results.run_benchmarks",
                return_value=[_result("working", 50.0, False)],
            ),
            patch("desktop_benchmarks.baseline.save_baseline", return_value=True),
        ):
            benchmark_desktop.main()
