import subprocess
from unittest.mock import MagicMock, patch

import benchmark_core
import benchmark_rebuild
import rebuild_benchmarks.execution
from benchmark_core import CommandMeasurement


def _empty_results_file(tmp_path):
    results_file = tmp_path / "results.csv"
    results_file.write_text(benchmark_rebuild.CSV_HEADER + "\n")
    return results_file


class TestBenchmarkCommands:
    def test_every_measured_command_names_only_the_host_being_benchmarked(self):
        kira = benchmark_core.BenchmarkTarget(
            "kira", "darwin", "darwinConfigurations.kira.system"
        )
        commands = rebuild_benchmarks.execution.get_benchmark_commands(kira)

        for benchmark_type in ("eval", "dry-run", "build"):
            assert kira.flake_output in commands[benchmark_type], benchmark_type

    def test_eval_measures_the_host_configuration_without_building_it(self):
        chise = benchmark_core.BenchmarkTarget(
            "chise", "nixos", "nixosConfigurations.chise.config.system.build.toplevel"
        )
        eval_command = rebuild_benchmarks.execution.get_benchmark_commands(chise)["eval"]

        assert eval_command.startswith("nix eval ")
        assert eval_command.endswith(f"#{chise.flake_output}.drvPath --raw")

    def test_every_command_reads_the_flake_with_its_private_submodule(self):
        kira = benchmark_core.BenchmarkTarget(
            "kira", "darwin", "darwinConfigurations.kira.system"
        )
        commands = rebuild_benchmarks.execution.get_benchmark_commands(kira)

        for benchmark_type in ("eval", "dry-run", "build"):
            assert "git+file://" in commands[benchmark_type], benchmark_type
            assert "?submodules=1#" in commands[benchmark_type], benchmark_type


class TestRecordBenchmarkResult:
    def test_appends_csv_line(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        rebuild_benchmarks.execution.record_benchmark_result(
            results_file, "eval", "kira/darwin", 1.234, "abc1234"
        )

        lines = results_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "eval" in lines[1]
        assert "kira/darwin" in lines[1]
        assert "1.234" in lines[1]
        assert "abc1234" in lines[1]


class TestRunAndRecordBenchmark:
    def test_records_a_successful_command(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        with (
            patch(
                "benchmark_core.measure_shell_command",
                return_value=CommandMeasurement(True, 2.5),
            ),
            patch(
                "benchmark_core.get_current_git_short_commit",
                return_value="abc1234",
            ),
        ):
            measurement = rebuild_benchmarks.execution.run_and_record_benchmark(
                "eval", "true", "kira/darwin", results_file
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
            measurement = rebuild_benchmarks.execution.run_and_record_benchmark(
                "eval", "false", "kira/darwin", results_file
            )

        assert measurement.succeeded is False
        assert results_file.read_text() == benchmark_rebuild.CSV_HEADER + "\n"

    def test_records_nothing_when_the_command_times_out(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        with patch(
            "benchmark_core.subprocess.run",
            side_effect=subprocess.TimeoutExpired("nix", 1),
        ):
            measurement = rebuild_benchmarks.execution.run_and_record_benchmark(
                "eval", "sleep 100", "kira/darwin", results_file
            )

        assert measurement.succeeded is False
        assert results_file.read_text() == benchmark_rebuild.CSV_HEADER + "\n"

    def test_records_nothing_when_the_command_cannot_start(self, tmp_path):
        results_file = _empty_results_file(tmp_path)

        with patch(
            "benchmark_core.subprocess.run",
            side_effect=OSError("no such binary"),
        ):
            measurement = rebuild_benchmarks.execution.run_and_record_benchmark(
                "eval", "absent-binary", "kira/darwin", results_file
            )

        assert measurement.succeeded is False
        assert results_file.read_text() == benchmark_rebuild.CSV_HEADER + "\n"
