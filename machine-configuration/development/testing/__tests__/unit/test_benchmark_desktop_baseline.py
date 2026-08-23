import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import benchmark_desktop


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _fresh_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TestTrackedBaselinePath:
    def test_resolves_a_baseline_that_exists_in_the_checkout(self):
        relative_path = benchmark_desktop.BASELINE_PATH.relative_to(
            benchmark_desktop.DOTFILES_DIRECTORY
        )
        assert (_repository_root() / relative_path).is_file()


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


class TestCheckBaseline:
    def _make_baseline(self, tmp_path, measurements=None, generated_at=None):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(
            json.dumps(
                {
                    "generated_at": generated_at or _fresh_timestamp(),
                    "git_commit": "abc123",
                    "threshold_percent": 200,
                    "measurements": measurements
                    if measurements is not None
                    else {"test": {"avg_ms": 50, "max_allowed_ms": 100}},
                }
            )
        )
        return baseline_file

    def test_fails_when_no_file(self, tmp_path):
        with patch.object(benchmark_desktop, "BASELINE_PATH", tmp_path / "nope.json"):
            assert benchmark_desktop.check_baseline() is False

    def test_fails_without_raising_on_malformed_json(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text("{ not json")

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            assert benchmark_desktop.check_baseline() is False

    def test_passes_without_any_results_csv_or_desktop_session(self, tmp_path):
        baseline_file = self._make_baseline(tmp_path)

        with (
            patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file),
            patch.object(benchmark_desktop, "RESULTS_DIRECTORY", tmp_path / "absent"),
            patch.dict("os.environ", {}, clear=True),
        ):
            assert benchmark_desktop.check_baseline() is True

    def test_fails_when_the_baseline_is_stale(self, tmp_path):
        baseline_file = self._make_baseline(
            tmp_path, generated_at="2025-01-01T00:00:00+00:00"
        )

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            assert benchmark_desktop.check_baseline() is False

    def test_fails_when_a_ceiling_is_not_positive(self, tmp_path):
        baseline_file = self._make_baseline(
            tmp_path, {"comp": {"avg_ms": 5, "max_allowed_ms": 0}}
        )

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            assert benchmark_desktop.check_baseline() is False

    def test_fails_when_no_measurements(self, tmp_path):
        baseline_file = self._make_baseline(tmp_path, {})

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            assert benchmark_desktop.check_baseline() is False


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
