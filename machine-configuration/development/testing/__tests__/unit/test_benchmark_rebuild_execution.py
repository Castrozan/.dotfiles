import subprocess
from unittest.mock import MagicMock, patch

import benchmark_rebuild
from benchmark_core import CommandMeasurement


def _empty_results_file(tmp_path):
    results_file = tmp_path / "results.csv"
    results_file.write_text(benchmark_rebuild.CSV_HEADER + "\n")
    return results_file


class TestRecordBenchmarkResult:
    def test_appends_csv_line(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        benchmark_rebuild.record_benchmark_result(
            results_file, "eval", "home", 1.234, "abc1234"
        )

        lines = results_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "eval" in lines[1]
        assert "home" in lines[1]
        assert "1.234" in lines[1]
        assert "abc1234" in lines[1]


class TestRunAndRecordBenchmark:
    def test_records_a_successful_command(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        with (
            patch(
                "benchmark_rebuild.measure_shell_command",
                return_value=CommandMeasurement(True, 2.5),
            ),
            patch(
                "benchmark_rebuild.get_current_git_short_commit",
                return_value="abc1234",
            ),
        ):
            measurement = benchmark_rebuild.run_and_record_benchmark(
                "eval", "true", "darwin", results_file
            )

        assert measurement.succeeded is True
        lines = results_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "2.500" in lines[1]

    def test_records_nothing_for_a_non_zero_command(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=1),
        ):
            measurement = benchmark_rebuild.run_and_record_benchmark(
                "eval", "false", "darwin", results_file
            )

        assert measurement.succeeded is False
        assert results_file.read_text() == benchmark_rebuild.CSV_HEADER + "\n"

    def test_records_nothing_when_the_command_times_out(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        with patch(
            "benchmark_core.subprocess.run",
            side_effect=subprocess.TimeoutExpired("nix", 1),
        ):
            measurement = benchmark_rebuild.run_and_record_benchmark(
                "eval", "sleep 100", "darwin", results_file
            )

        assert measurement.succeeded is False
        assert results_file.read_text() == benchmark_rebuild.CSV_HEADER + "\n"

    def test_records_nothing_when_the_command_cannot_start(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        with patch(
            "benchmark_core.subprocess.run",
            side_effect=OSError("no such binary"),
        ):
            measurement = benchmark_rebuild.run_and_record_benchmark(
                "eval", "absent-binary", "darwin", results_file
            )

        assert measurement.succeeded is False
        assert results_file.read_text() == benchmark_rebuild.CSV_HEADER + "\n"
