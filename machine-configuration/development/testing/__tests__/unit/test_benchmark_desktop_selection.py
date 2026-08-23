from unittest.mock import patch

import benchmark_desktop


class TestParseArguments:
    def test_defaults(self):
        command, iterations, component = benchmark_desktop.parse_arguments([])
        assert command == "run"
        assert iterations == 5
        assert component is None

    def test_save_baseline(self):
        command, _, _ = benchmark_desktop.parse_arguments(["--save-baseline"])
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
        benchmarks = [("tmux-new", None), ("tmux-split", None), ("wezterm", None)]
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
            assert "wezterm-launch" in names

    def test_returns_terminal_only_when_no_hyprland(self):
        with patch("benchmark_desktop.is_hyprland_running", return_value=False):
            result = benchmark_desktop.get_available_benchmarks()
            names = [n for n, _ in result]
            assert "hyprctl-ipc" not in names
            assert "wezterm-launch" in names
