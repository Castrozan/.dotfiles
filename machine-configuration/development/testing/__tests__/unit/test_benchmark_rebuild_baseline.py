import json
from datetime import datetime, timezone
from unittest.mock import patch

import benchmark_rebuild
from benchmark_baseline import BaselineValidation


def _valid_baseline() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": "abc1234",
        "config": "home",
        "threshold_percent": 150,
        "measurements": {"eval": {"duration_seconds": 2.0, "max_allowed_seconds": 3.0}},
    }


class TestTrackedBaselinePath:
    def test_resolves_a_baseline_that_exists_in_the_checkout(self, repository_root):
        relative_path = benchmark_rebuild.BASELINE_PATH.relative_to(
            benchmark_rebuild.DOTFILES_DIRECTORY
        )
        assert (repository_root / relative_path).is_file()


class TestCheckBaselineReporting:
    def test_reports_tracked_measurements_without_any_local_results_csv(
        self, tmp_path, capsys
    ):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps(_valid_baseline()))

        with (
            patch("benchmark_rebuild.BASELINE_PATH", baseline_file),
            patch("benchmark_rebuild.RESULTS_DIRECTORY", tmp_path / "absent"),
        ):
            assert benchmark_rebuild.check_baseline() is True

        report = capsys.readouterr().out
        assert "Commit: abc1234" in report
        assert "Threshold: 150%" in report
        assert "eval: 2.0s (max 3.0s)" in report
        assert "PASSED" in report


class TestCheckBaselineDelegatesValidation:
    def test_fails_and_prints_every_failure_the_validator_reports(self, capsys):
        validation = BaselineValidation({}, None, ["first problem", "second problem"])

        with patch(
            "benchmark_rebuild.validate_tracked_baseline", return_value=validation
        ):
            assert benchmark_rebuild.check_baseline() is False

        report = capsys.readouterr().out
        assert "FAILED (2 issues)" in report
        assert "- first problem" in report
        assert "- second problem" in report

    def test_asks_the_validator_for_the_tracked_path_and_rebuild_keys(self):
        validation = BaselineValidation({}, None, ["stubbed"])

        with patch(
            "benchmark_rebuild.validate_tracked_baseline", return_value=validation
        ) as validate:
            benchmark_rebuild.check_baseline()

        validate.assert_called_once_with(
            benchmark_rebuild.BASELINE_PATH,
            "duration_seconds",
            "max_allowed_seconds",
            benchmark_rebuild.SAVE_BASELINE_COMMAND,
        )
