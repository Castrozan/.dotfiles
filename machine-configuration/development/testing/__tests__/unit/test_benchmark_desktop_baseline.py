import json
from datetime import datetime, timedelta, timezone
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


class TestCheckBaselineIgnoresAge:
    def test_passes_on_a_structurally_valid_but_stale_baseline(self, tmp_path, capsys):
        stale = datetime.now(timezone.utc) - timedelta(days=200)
        document = _valid_baseline()
        document["generated_at"] = stale.isoformat(timespec="seconds")
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps(document))

        with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
            assert benchmark_desktop.check_baseline() is True

        report = capsys.readouterr().out
        assert "Age: 200 days" in report
        assert "PASSED" in report
