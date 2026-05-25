from unittest.mock import patch, MagicMock

import benchmark_rebuild


class TestGetCurrentGitShortCommit:
    def test_returns_commit_hash(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc1234\n"
        with patch(
            "benchmark_rebuild.subprocess.run",
            return_value=mock_result,
        ):
            assert benchmark_rebuild.get_current_git_short_commit() == "abc1234"

    def test_returns_unknown_on_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch(
            "benchmark_rebuild.subprocess.run",
            return_value=mock_result,
        ):
            assert benchmark_rebuild.get_current_git_short_commit() == "unknown"


class TestRunBenchmarkCommand:
    def test_returns_elapsed_time(self):
        with patch("benchmark_rebuild.subprocess.run"):
            duration = benchmark_rebuild.run_benchmark_command("echo test")
            assert isinstance(duration, float)
            assert duration >= 0


class TestRecordBenchmarkResult:
    def test_appends_csv_line(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("timestamp,type,config,duration_seconds,commit\n")

        benchmark_rebuild.record_benchmark_result(
            results_file, "eval", "home", 1.234, "abc1234"
        )

        content = results_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "eval" in lines[1]
        assert "home" in lines[1]
        assert "1.234" in lines[1]
        assert "abc1234" in lines[1]


class TestInitializeCsvIfNeeded:
    def test_creates_file_with_header(self, tmp_path):
        results_file = tmp_path / "results.csv"
        benchmark_rebuild.initialize_csv_if_needed(results_file)
        content = results_file.read_text()
        assert content.startswith("timestamp,type,config")

    def test_does_not_overwrite_existing(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("existing data\n")
        benchmark_rebuild.initialize_csv_if_needed(results_file)
        assert results_file.read_text() == "existing data\n"
