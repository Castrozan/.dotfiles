import datetime
import json
from pathlib import Path
from unittest.mock import patch

import benchmark_rebuild


def _isoformat_recent_baseline_timestamp_within_freshness_window() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[5]


class TestTrackedBaselinePath:
    def test_resolves_a_baseline_that_exists_in_the_checkout(self):
        relative_path = benchmark_rebuild.BASELINE_PATH.relative_to(
            benchmark_rebuild.DOTFILES_DIRECTORY
        )
        assert (_repository_root() / relative_path).is_file()


class TestCheckBaseline:
    def _write_baseline(self, tmp_path, baseline) -> Path:
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps(baseline))
        return baseline_file

    def test_fails_when_no_baseline_file(self, tmp_path):
        with patch(
            "benchmark_rebuild.BASELINE_PATH",
            tmp_path / "nonexistent.json",
        ):
            assert benchmark_rebuild.check_baseline() is False

    def test_fails_without_raising_on_malformed_json(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text("{ not json")

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is False

    def test_fails_without_raising_on_a_measurement_missing_its_value(self, tmp_path):
        baseline_file = self._write_baseline(
            tmp_path,
            {
                "generated_at": (
                    _isoformat_recent_baseline_timestamp_within_freshness_window()
                ),
                "measurements": {"eval": {"max_allowed_seconds": 3.0}},
            },
        )

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is False

    def test_passes_without_any_local_results_csv(self, tmp_path):
        baseline_file = self._write_baseline(
            tmp_path,
            {
                "generated_at": (
                    _isoformat_recent_baseline_timestamp_within_freshness_window()
                ),
                "git_commit": "abc1234",
                "config": "home",
                "threshold_percent": 150,
                "measurements": {
                    "eval": {
                        "duration_seconds": 2.0,
                        "max_allowed_seconds": 3.0,
                    },
                    "rebuild": {
                        "duration_seconds": 12.0,
                        "max_allowed_seconds": 18.0,
                    },
                },
            },
        )

        with (
            patch("benchmark_rebuild.BASELINE_PATH", baseline_file),
            patch("benchmark_rebuild.RESULTS_DIRECTORY", tmp_path / "absent"),
        ):
            assert benchmark_rebuild.check_baseline() is True

    def test_fails_when_baseline_too_old(self, tmp_path):
        baseline_file = self._write_baseline(
            tmp_path,
            {
                "generated_at": "2025-01-01T00:00:00+00:00",
                "git_commit": "abc1234",
                "config": "home",
                "threshold_percent": 150,
                "measurements": {
                    "eval": {
                        "duration_seconds": 2.0,
                        "max_allowed_seconds": 3.0,
                    },
                },
            },
        )

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is False

    def test_fails_when_no_measurements(self, tmp_path):
        baseline_file = self._write_baseline(
            tmp_path,
            {
                "generated_at": (
                    _isoformat_recent_baseline_timestamp_within_freshness_window()
                ),
                "git_commit": "abc1234",
                "config": "home",
                "threshold_percent": 150,
                "measurements": {},
            },
        )

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is False

    def test_fails_when_a_ceiling_is_not_positive(self, tmp_path):
        baseline_file = self._write_baseline(
            tmp_path,
            {
                "generated_at": (
                    _isoformat_recent_baseline_timestamp_within_freshness_window()
                ),
                "git_commit": "abc1234",
                "config": "home",
                "threshold_percent": 150,
                "measurements": {
                    "eval": {
                        "duration_seconds": 2.0,
                        "max_allowed_seconds": 0,
                    },
                },
            },
        )

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is False
