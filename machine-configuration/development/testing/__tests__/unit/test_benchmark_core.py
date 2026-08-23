import subprocess
from unittest.mock import MagicMock, patch

import benchmark_core


class TestTrackedBaselineDirectory:
    def test_resolves_committed_rebuild_baseline_inside_the_checkout(self):
        baseline_path = benchmark_core.TRACKED_BASELINE_DIRECTORY / "baseline.json"
        relative_path = baseline_path.relative_to(benchmark_core.DOTFILES_DIRECTORY)
        assert str(relative_path) == (
            "machine-configuration/development/testing/baseline.json"
        )

    def test_resolves_committed_desktop_baseline_inside_the_checkout(self):
        baseline_path = (
            benchmark_core.TRACKED_BASELINE_DIRECTORY / "baseline-desktop.json"
        )
        relative_path = baseline_path.relative_to(benchmark_core.DOTFILES_DIRECTORY)
        assert str(relative_path) == (
            "machine-configuration/development/testing/baseline-desktop.json"
        )


class TestMeasureCommand:
    def test_reports_success_for_zero_exit_status(self):
        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=0),
        ):
            measurement = benchmark_core.measure_command(["true"])

        assert measurement.succeeded is True
        assert measurement.elapsed_seconds >= 0

    def test_reports_failure_for_non_zero_exit_status(self):
        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=3),
        ):
            measurement = benchmark_core.measure_command(["false"])

        assert measurement.succeeded is False

    def test_reports_failure_on_timeout(self):
        with patch(
            "benchmark_core.subprocess.run",
            side_effect=subprocess.TimeoutExpired("qs", 5),
        ):
            measurement = benchmark_core.measure_command(["qs"], timeout_seconds=5)

        assert measurement.succeeded is False
        assert measurement.elapsed_seconds >= 0

    def test_reports_failure_on_operating_system_error(self):
        with patch(
            "benchmark_core.subprocess.run",
            side_effect=OSError("missing binary"),
        ):
            measurement = benchmark_core.measure_command(["absent"])

        assert measurement.succeeded is False


class TestMeasureShellCommand:
    def test_reports_failure_for_non_zero_exit_status(self):
        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=1),
        ) as mock_run:
            measurement = benchmark_core.measure_shell_command("exit 1")

        assert measurement.succeeded is False
        assert mock_run.call_args.kwargs["shell"] is True

    def test_reports_success_for_zero_exit_status(self):
        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=0),
        ):
            measurement = benchmark_core.measure_shell_command("true")

        assert measurement.succeeded is True


class TestUnmeasurableCommand:
    def test_carries_no_elapsed_time(self):
        measurement = benchmark_core.unmeasurable_command()
        assert measurement.succeeded is False
        assert measurement.elapsed_seconds == 0.0


class TestGetCurrentGitShortCommit:
    def test_returns_commit_hash(self):
        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="abc1234\n"),
        ):
            assert benchmark_core.get_current_git_short_commit() == "abc1234"

    def test_returns_unknown_on_failure(self):
        with patch(
            "benchmark_core.subprocess.run",
            return_value=MagicMock(returncode=1),
        ):
            assert benchmark_core.get_current_git_short_commit() == "unknown"


class TestEnsureResultsFileExists:
    def test_creates_missing_directory_and_header(self, tmp_path):
        results_file = tmp_path / "nested" / "results.csv"
        benchmark_core.ensure_results_file_exists(results_file, "timestamp,type")
        assert results_file.read_text() == "timestamp,type\n"

    def test_does_not_overwrite_existing(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("existing data\n")
        benchmark_core.ensure_results_file_exists(results_file, "timestamp,type")
        assert results_file.read_text() == "existing data\n"


class TestAppendResultRow:
    def test_prefixes_the_local_timestamp(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("timestamp,type\n")

        with patch(
            "benchmark_core.local_result_timestamp",
            return_value="2026-08-23T10:00:00-03:00",
        ):
            benchmark_core.append_result_row(results_file, ["eval", "1.500"])

        assert results_file.read_text().splitlines()[1] == (
            "2026-08-23T10:00:00-03:00,eval,1.500"
        )


class TestUtcBaselineTimestamp:
    def test_is_timezone_aware_and_second_precision(self):
        timestamp = benchmark_core.utc_baseline_timestamp()
        assert timestamp.endswith("+00:00")
        assert len(timestamp) == len("2026-08-23T10:00:00+00:00")
