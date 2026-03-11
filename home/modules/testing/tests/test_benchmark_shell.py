from unittest.mock import patch, MagicMock

import benchmark_shell


class TestIsShellAvailable:
    def test_returns_true_when_found(self):
        with patch("benchmark_shell.shutil.which", return_value="/usr/bin/bash"):
            assert benchmark_shell.is_shell_available("bash") is True

    def test_returns_false_when_not_found(self):
        with patch("benchmark_shell.shutil.which", return_value=None):
            assert benchmark_shell.is_shell_available("zsh") is False


class TestMeasureSingleShellStartup:
    def test_returns_positive_float(self):
        with patch("benchmark_shell.subprocess.run"):
            result = benchmark_shell.measure_single_shell_startup("bash")
            assert isinstance(result, float)
            assert result >= 0


class TestBenchmarkShellStartup:
    def test_returns_average_and_times(self):
        with patch(
            "benchmark_shell.measure_single_shell_startup",
            return_value=0.1,
        ):
            average, times = benchmark_shell.benchmark_shell_startup("bash", 3)
            assert len(times) == 3
            assert all(t == 0.1 for t in times)
            assert abs(average - 0.1) < 0.001


class TestRecordShellBenchmarkResult:
    def test_appends_csv_line(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("timestamp,shell,avg_seconds,iterations\n")

        benchmark_shell.record_shell_benchmark_result(
            results_file, "bash", 0.123456, 10
        )

        content = results_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "bash" in lines[1]
        assert "0.123456" in lines[1]
        assert "10" in lines[1]


class TestFormatIndividualTimes:
    def test_formats_times(self):
        result = benchmark_shell.format_individual_times([0.1, 0.2, 0.3])
        assert result == "0.100 0.200 0.300"

    def test_empty_list(self):
        assert benchmark_shell.format_individual_times([]) == ""


class TestDetermineShellsToBenchmark:
    def test_returns_default_shells_for_none(self):
        result = benchmark_shell.determine_shells_to_benchmark(None)
        assert result == ["bash", "fish"]

    def test_returns_default_shells_for_all(self):
        result = benchmark_shell.determine_shells_to_benchmark("all")
        assert result == ["bash", "fish"]

    def test_returns_specific_shell(self):
        result = benchmark_shell.determine_shells_to_benchmark("zsh")
        assert result == ["zsh"]


class TestParseArguments:
    def test_defaults(self):
        iterations, shells = benchmark_shell.parse_arguments([])
        assert iterations == 10
        assert shells == ["bash", "fish"]

    def test_custom_iterations(self):
        iterations, shells = benchmark_shell.parse_arguments(["5"])
        assert iterations == 5

    def test_custom_iterations_and_shell(self):
        iterations, shells = benchmark_shell.parse_arguments(["20", "zsh"])
        assert iterations == 20
        assert shells == ["zsh"]

    def test_invalid_iterations_exits(self):
        try:
            benchmark_shell.parse_arguments(["abc"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1


class TestInitializeCsvIfNeeded:
    def test_creates_file_with_header(self, tmp_path):
        results_file = tmp_path / "results.csv"
        benchmark_shell.initialize_csv_if_needed(results_file)
        content = results_file.read_text()
        assert content.startswith("timestamp,shell")

    def test_does_not_overwrite_existing(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("existing data\n")
        benchmark_shell.initialize_csv_if_needed(results_file)
        assert results_file.read_text() == "existing data\n"


class TestMain:
    def test_skips_unavailable_shell(self, capsys):
        with patch("benchmark_shell.sys.argv", ["cmd", "1", "nonexistent"]):
            with patch(
                "benchmark_shell.get_results_file_path",
                return_value=MagicMock(),
            ):
                with patch("benchmark_shell.ensure_results_directory_exists"):
                    with patch("benchmark_shell.initialize_csv_if_needed"):
                        with patch(
                            "benchmark_shell.is_shell_available",
                            return_value=False,
                        ):
                            benchmark_shell.main()
                            output = capsys.readouterr().out
                            assert "Skipping" in output

    def test_runs_benchmark_for_available_shell(self):
        with patch("benchmark_shell.sys.argv", ["cmd", "1", "bash"]):
            with patch(
                "benchmark_shell.get_results_file_path",
                return_value=MagicMock(),
            ):
                with patch("benchmark_shell.ensure_results_directory_exists"):
                    with patch("benchmark_shell.initialize_csv_if_needed"):
                        with patch(
                            "benchmark_shell.is_shell_available",
                            return_value=True,
                        ):
                            with patch(
                                "benchmark_shell.benchmark_shell_startup",
                                return_value=(0.1, [0.1]),
                            ):
                                with patch(
                                    "benchmark_shell.record_shell_benchmark_result"
                                ) as mock_record:
                                    benchmark_shell.main()
                                    mock_record.assert_called_once()
