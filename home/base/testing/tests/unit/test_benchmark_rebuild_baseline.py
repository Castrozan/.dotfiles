import datetime
import json
from unittest.mock import patch

import benchmark_rebuild


def _isoformat_recent_baseline_timestamp_within_freshness_window() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class TestBuildBaselineFromMeasurements:
    def test_builds_correct_structure(self):
        with patch(
            "benchmark_rebuild.get_current_git_short_commit",
            return_value="abc1234",
        ):
            baseline = benchmark_rebuild.build_baseline_from_measurements(
                {"eval": 10.0, "rebuild": 20.0}, "home"
            )

        assert baseline["git_commit"] == "abc1234"
        assert baseline["config"] == "home"
        assert baseline["threshold_percent"] == 150
        assert baseline["measurements"]["eval"]["duration_seconds"] == 10.0
        assert baseline["measurements"]["eval"]["max_allowed_seconds"] == 15.0
        assert baseline["measurements"]["rebuild"]["duration_seconds"] == 20.0
        assert baseline["measurements"]["rebuild"]["max_allowed_seconds"] == 30.0


class TestCheckBaseline:
    def test_fails_when_no_baseline_file(self, tmp_path):
        with (
            patch(
                "benchmark_rebuild.BASELINE_PATH",
                tmp_path / "nonexistent.json",
            ),
            patch(
                "benchmark_rebuild.DOTFILES_DIRECTORY",
                tmp_path,
            ),
        ):
            assert benchmark_rebuild.check_baseline() is False

    def test_passes_with_valid_baseline(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline = {
            "generated_at": _isoformat_recent_baseline_timestamp_within_freshness_window(),
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
        }
        baseline_file.write_text(json.dumps(baseline))

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is True

    def test_fails_when_baseline_too_old(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline = {
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
        }
        baseline_file.write_text(json.dumps(baseline))

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is False

    def test_fails_when_no_measurements(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline = {
            "generated_at": _isoformat_recent_baseline_timestamp_within_freshness_window(),
            "git_commit": "abc1234",
            "config": "home",
            "threshold_percent": 150,
            "measurements": {},
        }
        baseline_file.write_text(json.dumps(baseline))

        with patch("benchmark_rebuild.BASELINE_PATH", baseline_file):
            assert benchmark_rebuild.check_baseline() is False
