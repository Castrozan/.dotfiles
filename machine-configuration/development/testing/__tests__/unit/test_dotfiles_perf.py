from unittest.mock import MagicMock, patch

import pytest

import dotfiles_perf


def _delegating(exit_code: int = 0):
    return patch("dotfiles_perf.run_delegated_command", return_value=exit_code)


def _invoke(arguments: list[str]) -> int:
    with patch("dotfiles_perf.sys.argv", ["dotfiles-perf", *arguments]):
        with pytest.raises(SystemExit) as exit_info:
            dotfiles_perf.main()
    return exit_info.value.code


class TestDelegation:
    def test_run_forwards_every_argument_to_the_desktop_benchmark(self):
        with _delegating() as delegate:
            _invoke(["run", "10", "tmux"])
        assert delegate.call_args[0][0] == ["benchmark-desktop", "10", "tmux"]

    def test_check_compares_the_latest_run_against_the_baseline(self):
        with _delegating() as delegate:
            _invoke(["check"])
        assert delegate.call_args[0][0] == ["benchmark-desktop", "--compare-latest"]

    def test_validate_checks_the_tracked_baseline(self):
        with _delegating() as delegate:
            _invoke(["validate"])
        assert delegate.call_args[0][0] == ["benchmark-desktop", "--check-baseline"]

    def test_baseline_saves_a_new_baseline(self):
        with _delegating() as delegate:
            _invoke(["baseline"])
        assert delegate.call_args[0][0] == ["benchmark-desktop", "--save-baseline"]

    def test_report_shows_the_benchmark_history(self):
        with _delegating() as delegate:
            _invoke(["report"])
        assert delegate.call_args[0][0] == ["benchmark-desktop", "report"]

    def test_shell_forwards_every_argument_to_the_shell_benchmark(self):
        with _delegating() as delegate:
            _invoke(["shell", "20", "fish"])
        assert delegate.call_args[0][0] == ["benchmark-shell", "20", "fish"]

    def test_rebuild_forwards_every_argument_to_the_rebuild_benchmark(self):
        with _delegating() as delegate:
            _invoke(["rebuild", "eval"])
        assert delegate.call_args[0][0] == ["benchmark-rebuild", "eval"]

    def test_propagates_the_delegated_exit_status(self):
        with _delegating(3):
            assert _invoke(["run"]) == 3


class TestUnavailableDelegate:
    def test_reports_an_absent_command_with_the_not_found_status(self, capsys):
        with patch("dotfiles_perf.shutil.which", return_value=None):
            status = dotfiles_perf.run_delegated_command(["benchmark-desktop"])

        assert status == dotfiles_perf.COMMAND_NOT_FOUND_STATUS
        assert "benchmark-desktop is not available" in capsys.readouterr().err

    def test_returns_the_exit_status_of_a_command_that_ran(self):
        with (
            patch("dotfiles_perf.shutil.which", return_value="/usr/bin/true"),
            patch(
                "dotfiles_perf.subprocess.run",
                return_value=MagicMock(returncode=4),
            ),
        ):
            assert dotfiles_perf.run_delegated_command(["benchmark-desktop"]) == 4

    def test_an_absent_delegate_fails_the_command_that_asked_for_it(self):
        with patch("dotfiles_perf.shutil.which", return_value=None):
            assert _invoke(["run"]) == dotfiles_perf.COMMAND_NOT_FOUND_STATUS


class TestThresholdTests:
    def test_runs_every_discovered_threshold_test_file(self):
        with (
            patch(
                "dotfiles_perf.find_threshold_test_files",
                return_value=["/a/perf-runtime.bats", "/b/perf-runtime.bats"],
            ),
            _delegating() as delegate,
        ):
            _invoke(["test"])

        assert delegate.call_args[0][0] == [
            "bats",
            "/a/perf-runtime.bats",
            "/b/perf-runtime.bats",
        ]

    def test_fails_when_no_threshold_test_file_exists(self, capsys):
        with patch("dotfiles_perf.find_threshold_test_files", return_value=[]):
            assert _invoke(["test"]) == 1
        assert "perf-runtime.bats" in capsys.readouterr().err

    def test_searches_the_configuration_tree_of_the_checkout(self):
        assert dotfiles_perf.THRESHOLD_TEST_ROOT.name == "machine-configuration"


class TestFullSuite:
    def test_measures_then_compares_then_runs_the_threshold_tests(self):
        with (
            patch(
                "dotfiles_perf.find_threshold_test_files",
                return_value=["/a/perf-runtime.bats"],
            ),
            _delegating() as delegate,
        ):
            _invoke(["all"])

        delegated = [call[0][0] for call in delegate.call_args_list]
        assert delegated == [
            ["benchmark-desktop", "5"],
            ["benchmark-desktop", "--compare-latest"],
            ["bats", "/a/perf-runtime.bats"],
        ]

    def test_forwards_a_requested_iteration_count(self):
        with (
            patch("dotfiles_perf.find_threshold_test_files", return_value=["/a.bats"]),
            _delegating() as delegate,
        ):
            _invoke(["all", "12"])

        assert delegate.call_args_list[0][0][0] == ["benchmark-desktop", "12"]

    def test_stops_at_a_failed_measurement(self):
        with _delegating(2) as delegate:
            assert _invoke(["all"]) == 2
        assert delegate.call_count == 1

    def test_stops_at_a_regression_before_the_threshold_tests(self):
        statuses = iter([0, 1])
        with patch(
            "dotfiles_perf.run_delegated_command",
            side_effect=lambda _arguments: next(statuses),
        ) as delegate:
            assert _invoke(["all"]) == 1
        assert delegate.call_count == 2


class TestUsage:
    @pytest.mark.parametrize("arguments", [[], ["-h"], ["--help"]])
    def test_prints_usage_without_failing(self, arguments, capsys):
        with patch("dotfiles_perf.sys.argv", ["dotfiles-perf", *arguments]):
            dotfiles_perf.main()
        assert "Usage: dotfiles-perf" in capsys.readouterr().out

    def test_an_unknown_command_fails_with_an_actionable_message(self, capsys):
        assert _invoke(["bogus"]) == 1
        captured = capsys.readouterr()
        assert "Unknown command: bogus" in captured.err
        assert "Usage: dotfiles-perf" in captured.out
