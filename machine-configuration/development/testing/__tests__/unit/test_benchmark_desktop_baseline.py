import json
from datetime import datetime, timezone
from unittest.mock import patch

import benchmark_desktop
from benchmark_baseline import BaselineValidation


def _valid_baseline() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": "abc123",
        "host": "chise",
        "config": "nixos",
        "threshold_percent": 200,
        "measurements": {"wezterm": {"avg_ms": 50, "max_allowed_ms": 100}},
    }


class TestTrackedBaselinePath:
    def test_resolves_a_baseline_that_exists_in_the_checkout(self, repository_root):
        relative_path = benchmark_desktop.BASELINE_PATH.relative_to(
            benchmark_desktop.DOTFILES_DIRECTORY
        )
        assert (repository_root / relative_path).is_file()


class TestCheckBaselineReporting:
    def test_reports_tracked_measurements_without_a_csv_or_desktop_session(
        self, tmp_path, capsys
    ):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps(_valid_baseline()))

        with (
            patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file),
            patch.object(benchmark_desktop, "RESULTS_DIRECTORY", tmp_path / "absent"),
            patch.dict("os.environ", {}, clear=True),
        ):
            assert benchmark_desktop.check_baseline() is True

        report = capsys.readouterr().out
        assert "Commit: abc123" in report
        assert "Host: chise/nixos" in report
        assert "Threshold: 200%" in report
        assert "wezterm" in report
        assert "50ms" in report
        assert "100ms" in report
        assert "PASSED" in report


class TestCheckBaselineDelegatesValidation:
    def test_fails_and_prints_every_failure_the_validator_reports(self, capsys):
        validation = BaselineValidation({}, None, ["first problem", "second problem"])

        with patch.object(
            benchmark_desktop, "validate_tracked_baseline", return_value=validation
        ):
            assert benchmark_desktop.check_baseline() is False

        report = capsys.readouterr().out
        assert "FAILED (2 issues)" in report
        assert "- first problem" in report
        assert "- second problem" in report

    def test_asks_the_validator_for_the_tracked_path_and_desktop_keys(self):
        validation = BaselineValidation({}, None, ["stubbed"])

        with patch.object(
            benchmark_desktop, "validate_tracked_baseline", return_value=validation
        ) as validate:
            benchmark_desktop.check_baseline()

        validate.assert_called_once_with(
            benchmark_desktop.BASELINE_PATH,
            "avg_ms",
            "max_allowed_ms",
            benchmark_desktop.SAVE_BASELINE_COMMAND,
        )


class TestGetLatestResultsByComponent:
    def test_returns_empty_when_no_file(self, tmp_path):
        result = benchmark_desktop.get_latest_results_by_component(
            tmp_path / "nope.csv"
        )
        assert result == {}

    def test_parses_latest_per_component(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text(
            "timestamp,component,avg_ms,min_ms,max_ms,iterations\n"
            "2026-01-01,wezterm,300.0,250.0,350.0,5\n"
            "2026-01-02,wezterm,320.0,280.0,360.0,5\n"
            "2026-01-01,tmux,20.0,15.0,25.0,5\n"
        )
        result = benchmark_desktop.get_latest_results_by_component(results_file)
        assert result["wezterm"] == 320.0
        assert result["tmux"] == 20.0


class TestCompareLatestResultsToBaseline:
    def _baseline(self, measurements):
        return {"measurements": measurements}

    def test_reports_no_regression_within_the_ceiling(self):
        comparison = benchmark_desktop.compare_latest_results_to_baseline(
            self._baseline({"comp": {"avg_ms": 50, "max_allowed_ms": 100}}),
            {"comp": 80.0},
        )
        assert comparison.regression_messages == []
        assert comparison.missing_component_names == []

    def test_reports_a_component_over_its_ceiling(self):
        comparison = benchmark_desktop.compare_latest_results_to_baseline(
            self._baseline({"comp": {"avg_ms": 50, "max_allowed_ms": 100}}),
            {"comp": 150.0},
        )
        assert len(comparison.regression_messages) == 1
        assert "exceeds max" in comparison.regression_messages[0]

    def test_names_components_that_were_never_measured(self):
        comparison = benchmark_desktop.compare_latest_results_to_baseline(
            self._baseline(
                {
                    "comp-a": {"avg_ms": 50, "max_allowed_ms": 100},
                    "comp-b": {"avg_ms": 50, "max_allowed_ms": 100},
                }
            ),
            {"comp-a": 80.0},
        )
        assert comparison.regression_messages == []
        assert comparison.missing_component_names == ["comp-b"]

    def test_reports_every_component_missing_when_no_results_exist(self):
        comparison = benchmark_desktop.compare_latest_results_to_baseline(
            self._baseline({"comp": {"avg_ms": 50, "max_allowed_ms": 100}}),
            {},
        )
        assert comparison.missing_component_names == ["comp"]
