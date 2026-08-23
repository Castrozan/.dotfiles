import subprocess
from unittest.mock import MagicMock, patch

import benchmark_desktop
from benchmark_core import CommandMeasurement


def _empty_results_file(tmp_path):
    results_file = tmp_path / "results.csv"
    results_file.write_text(benchmark_desktop.CSV_HEADER + "\n")
    return results_file


class TestIsHyprlandRunning:
    def test_returns_true_when_set(self):
        with patch.dict("os.environ", {"HYPRLAND_INSTANCE_SIGNATURE": "abc"}):
            assert benchmark_desktop.is_hyprland_running() is True

    def test_returns_false_when_unset(self):
        with patch.dict("os.environ", {}, clear=True):
            assert benchmark_desktop.is_hyprland_running() is False


class TestMeasureIterations:
    def test_returns_stats(self):
        result = benchmark_desktop.measure_iterations(
            "test", lambda: CommandMeasurement(True, 0.01), 3
        )
        assert result["name"] == "test"
        assert result["avg"] == 10.0
        assert result["min"] == 10.0
        assert result["max"] == 10.0
        assert len(result["times"]) == 3
        assert result["error"] is False

    def test_handles_all_errors(self):
        def failing():
            raise OSError("fail")

        result = benchmark_desktop.measure_iterations("test", failing, 3)
        assert result["error"] is True
        assert result["times"] == []

    def test_drops_non_zero_exit_iterations(self):
        result = benchmark_desktop.measure_iterations(
            "test", lambda: CommandMeasurement(False, 0.5), 3
        )
        assert result["error"] is True
        assert result["times"] == []

    def test_keeps_only_the_successful_iterations(self):
        outcomes = [(True, 0.02), (False, 9.0), (True, 0.04)]
        measurements = iter([CommandMeasurement(*outcome) for outcome in outcomes])
        result = benchmark_desktop.measure_iterations(
            "test", lambda: next(measurements), 3
        )
        assert result["times"] == [20.0, 40.0]
        assert result["avg"] == 30.0


class TestBenchmarkedCommands:
    def test_a_failing_hyprctl_call_is_not_a_measurement(self):
        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=1),
        ):
            measurement = benchmark_desktop.bench_hyprctl_ipc()
        assert measurement.succeeded is False

    def test_a_timed_out_quickshell_toggle_is_not_a_measurement(self):
        with (
            patch(
                "benchmark_core.subprocess.run",
                side_effect=subprocess.TimeoutExpired("qs", 5),
            ),
            patch("benchmark_desktop.run_cleanup_command"),
            patch("benchmark_desktop.time.sleep"),
        ):
            measurement = benchmark_desktop.bench_dashboard()
        assert measurement.succeeded is False

    def test_workspace_switch_reports_no_measurement_when_the_query_fails(self):
        with patch(
            "benchmark_desktop.subprocess.run",
            return_value=MagicMock(returncode=1, stdout=""),
        ):
            measurement = benchmark_desktop.bench_workspace_switch()
        assert measurement.succeeded is False
        assert measurement.elapsed_seconds == 0.0

    def test_a_missing_fuzzel_binary_reports_no_measurement(self):
        with patch("benchmark_desktop.shutil.which", return_value=None):
            measurement = benchmark_desktop.bench_fuzzel_launch()
        assert measurement.succeeded is False
        assert measurement.elapsed_seconds == 0.0


class TestRunBenchmarks:
    def test_records_nothing_for_a_component_that_always_fails(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        benchmark_desktop.run_benchmarks(
            [("broken", lambda: CommandMeasurement(False, 1.0))], 2, results_file
        )

        assert results_file.read_text() == benchmark_desktop.CSV_HEADER + "\n"

    def test_records_a_component_that_succeeds(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        benchmark_desktop.run_benchmarks(
            [("working", lambda: CommandMeasurement(True, 0.05))], 2, results_file
        )

        lines = results_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "working" in lines[1]
        assert lines[1].endswith(",2")


class TestFormatMs:
    def test_milliseconds(self):
        assert benchmark_desktop.format_ms(42.3) == "42ms"

    def test_seconds(self):
        assert benchmark_desktop.format_ms(1500.0) == "1.50s"


class TestRecordResult:
    def test_appends_csv_line(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        benchmark_desktop.record_result(results_file, "test-comp", 42.1, 30.0, 55.2, 5)

        lines = results_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "test-comp" in lines[1]
        assert "42.1" in lines[1]
        assert lines[1].endswith(",5")
