import json
from unittest.mock import patch

import benchmark_rebuild
from benchmark_core import BenchmarkTarget, CommandMeasurement

KIRA = BenchmarkTarget("kira", "darwin", "darwinConfigurations.kira.system")


class TestBuildBaselineFromMeasurements:
    def test_builds_correct_structure(self):
        with patch(
            "benchmark_rebuild.get_current_git_short_commit",
            return_value="abc1234",
        ):
            baseline = benchmark_rebuild.build_baseline_from_measurements(
                {"eval": 10.0, "rebuild": 20.0}, KIRA
            )

        assert baseline["git_commit"] == "abc1234"
        assert baseline["host"] == "kira"
        assert baseline["config"] == "darwin"
        assert baseline["threshold_percent"] == 150
        assert baseline["measurements"]["eval"]["duration_seconds"] == 10.0
        assert baseline["measurements"]["eval"]["max_allowed_seconds"] == 15.0
        assert baseline["measurements"]["rebuild"]["duration_seconds"] == 20.0
        assert baseline["measurements"]["rebuild"]["max_allowed_seconds"] == 30.0


class TestSaveBaseline:
    def _results_file(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text(benchmark_rebuild.CSV_HEADER + "\n")
        return results_file

    def test_refuses_to_write_a_baseline_when_a_command_fails(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        results_file = self._results_file(tmp_path)

        with (
            patch("benchmark_rebuild.BASELINE_PATH", baseline_file),
            patch(
                "benchmark_rebuild.measure_shell_command",
                return_value=CommandMeasurement(False, 4.0),
            ),
        ):
            saved = benchmark_rebuild.save_baseline(
                {"eval": "false", "rebuild": "false"}, KIRA, results_file
            )

        assert saved is False
        assert not baseline_file.exists()
        assert results_file.read_text() == benchmark_rebuild.CSV_HEADER + "\n"

    def test_leaves_an_existing_baseline_untouched_when_a_command_fails(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text('{"kept": true}\n')
        results_file = self._results_file(tmp_path)

        with (
            patch("benchmark_rebuild.BASELINE_PATH", baseline_file),
            patch(
                "benchmark_rebuild.measure_shell_command",
                return_value=CommandMeasurement(False, 4.0),
            ),
        ):
            saved = benchmark_rebuild.save_baseline(
                {"eval": "false", "rebuild": "false"}, KIRA, results_file
            )

        assert saved is False
        assert baseline_file.read_text() == '{"kept": true}\n'

    def test_writes_a_baseline_when_every_command_succeeds(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        results_file = self._results_file(tmp_path)

        with (
            patch("benchmark_rebuild.BASELINE_PATH", baseline_file),
            patch(
                "benchmark_rebuild.measure_shell_command",
                return_value=CommandMeasurement(True, 4.0),
            ),
            patch(
                "benchmark_rebuild.get_current_git_short_commit",
                return_value="abc1234",
            ),
        ):
            saved = benchmark_rebuild.save_baseline(
                {"eval": "true", "rebuild": "true"}, KIRA, results_file
            )

        assert saved is True
        written = json.loads(baseline_file.read_text())
        assert written["measurements"]["eval"]["duration_seconds"] == 4.0
        assert written["host"] == "kira"
        assert written["config"] == "darwin"

    def test_records_the_measuring_host_beside_the_configuration_in_the_csv(
        self, tmp_path
    ):
        results_file = self._results_file(tmp_path)

        with (
            patch("benchmark_rebuild.BASELINE_PATH", tmp_path / "baseline.json"),
            patch(
                "benchmark_rebuild.measure_shell_command",
                return_value=CommandMeasurement(True, 4.0),
            ),
            patch(
                "benchmark_rebuild.get_current_git_short_commit",
                return_value="abc1234",
            ),
        ):
            benchmark_rebuild.save_baseline(
                {"eval": "true", "rebuild": "true"}, KIRA, results_file
            )

        recorded_rows = results_file.read_text().strip().split("\n")[1:]
        assert len(recorded_rows) == 2
        for row in recorded_rows:
            assert row.split(",")[2] == "kira/darwin"
