from unittest.mock import patch, MagicMock
import json

import benchmark_desktop


class TestIsHyprlandRunning:
    def test_returns_true_when_set(self):
        with patch.dict("os.environ", {"HYPRLAND_INSTANCE_SIGNATURE": "abc"}):
            assert benchmark_desktop.is_hyprland_running() is True

    def test_returns_false_when_unset(self):
        with patch.dict("os.environ", {}, clear=True):
            assert benchmark_desktop.is_hyprland_running() is False


class TestRunTimed:
    def test_returns_positive_float(self):
        with patch("benchmark_desktop.subprocess.run"):
            result = benchmark_desktop.run_timed(["echo", "hi"])
            assert isinstance(result, float)
            assert result >= 0


class TestMeasureIterations:
    def test_returns_stats(self):
        result = benchmark_desktop.measure_iterations("test", lambda: 10.0, 3)
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


class TestFormatMs:
    def test_milliseconds(self):
        assert benchmark_desktop.format_ms(42.3) == "42ms"

    def test_seconds(self):
        assert benchmark_desktop.format_ms(1500.0) == "1.50s"

    def test_negative(self):
        assert benchmark_desktop.format_ms(-1) == "N/A"


class TestRecordResult:
    def test_appends_csv_line(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text(benchmark_desktop.CSV_HEADER + "\n")

        benchmark_desktop.record_result(results_file, "test-comp", 42.1, 30.0, 55.2, 5)

        content = results_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "test-comp" in lines[1]
        assert "42.1" in lines[1]
        assert "5" in lines[1]


class TestInitializeCsvIfNeeded:
    def test_creates_file_with_header(self, tmp_path):
        results_file = tmp_path / "results.csv"
        benchmark_desktop.initialize_csv_if_needed(results_file)
        content = results_file.read_text()
        assert content.startswith("timestamp,component")

    def test_does_not_overwrite_existing(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("existing data\n")
        benchmark_desktop.initialize_csv_if_needed(results_file)
        assert results_file.read_text() == "existing data\n"


class TestParseArguments:
    def test_defaults(self):
        command, iterations, component = benchmark_desktop.parse_arguments([])
        assert command == "run"
        assert iterations == 5
        assert component is None

    def test_save_baseline(self):
        command, iterations, _ = benchmark_desktop.parse_arguments(["--save-baseline"])
        assert command == "save-baseline"

    def test_check_baseline(self):
        command, _, _ = benchmark_desktop.parse_arguments(["--check-baseline"])
        assert command == "check-baseline"

    def test_report(self):
        command, _, _ = benchmark_desktop.parse_arguments(["report"])
        assert command == "report"

    def test_custom_iterations(self):
        _, iterations, _ = benchmark_desktop.parse_arguments(["10"])
        assert iterations == 10

    def test_component_filter(self):
        _, _, component = benchmark_desktop.parse_arguments(["tmux"])
        assert component == "tmux"

    def test_iterations_and_component(self):
        _, iterations, component = benchmark_desktop.parse_arguments(["10", "tmux"])
        assert iterations == 10
        assert component == "tmux"


class TestFilterBenchmarks:
    def test_returns_all_when_no_filter(self):
        benchmarks = [("a", None), ("b", None)]
        result = benchmark_desktop.filter_benchmarks(benchmarks, None)
        assert len(result) == 2

    def test_filters_by_partial_match(self):
        benchmarks = [("tmux-new", None), ("tmux-split", None), ("fish", None)]
        result = benchmark_desktop.filter_benchmarks(benchmarks, "tmux")
        assert len(result) == 2

    def test_no_match_returns_empty(self):
        benchmarks = [("a", None), ("b", None)]
        result = benchmark_desktop.filter_benchmarks(benchmarks, "zzz")
        assert len(result) == 0


class TestGetAvailableBenchmarks:
    def test_returns_all_when_hyprland(self):
        with patch("benchmark_desktop.is_hyprland_running", return_value=True):
            result = benchmark_desktop.get_available_benchmarks()
            names = [n for n, _ in result]
            assert "hyprctl-ipc" in names
            assert "fish-startup" in names

    def test_returns_terminal_only_when_no_hyprland(self):
        with patch("benchmark_desktop.is_hyprland_running", return_value=False):
            result = benchmark_desktop.get_available_benchmarks()
            names = [n for n, _ in result]
            assert "hyprctl-ipc" not in names
            assert "fish-startup" in names


class TestCheckBaseline:
    def test_fails_when_no_file(self, tmp_path):
        with patch.object(benchmark_desktop, "BASELINE_PATH", tmp_path / "nope.json"):
            with patch.object(benchmark_desktop, "DOTFILES_DIRECTORY", tmp_path):
                assert benchmark_desktop.check_baseline() is False

    def test_passes_with_valid_baseline(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        from datetime import datetime, timezone
        baseline = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "git_commit": "abc123",
            "threshold_percent": 200,
            "measurements": {
                "test": {"avg_ms": 50, "max_allowed_ms": 100}
            },
        }
        baseline_file.write_text(json.dumps(baseline))

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            with patch.object(benchmark_desktop, "DOTFILES_DIRECTORY", tmp_path):
                assert benchmark_desktop.check_baseline() is True


class TestSaveBaseline:
    def test_writes_baseline_file(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        results = [
            {"name": "test", "avg": 50.0, "min": 40.0, "max": 60.0, "times": [50.0], "error": False},
        ]

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            with patch("benchmark_desktop._get_git_commit", return_value="abc"):
                benchmark_desktop.save_baseline(results)

        data = json.loads(baseline_file.read_text())
        assert "test" in data["measurements"]
        assert data["measurements"]["test"]["avg_ms"] == 50.0

    def test_skips_errored_results(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        results = [
            {"name": "ok", "avg": 50.0, "min": 40.0, "max": 60.0, "times": [50.0], "error": False},
            {"name": "bad", "avg": 0, "min": 0, "max": 0, "times": [], "error": True},
        ]

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            with patch("benchmark_desktop._get_git_commit", return_value="abc"):
                benchmark_desktop.save_baseline(results)

        data = json.loads(baseline_file.read_text())
        assert "ok" in data["measurements"]
        assert "bad" not in data["measurements"]
