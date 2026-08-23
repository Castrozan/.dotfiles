import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

import benchmark_desktop

CSV_ROWS = "timestamp,component,avg_ms,min_ms,max_ms,iterations\n"


def _tracked_baseline(**measurements) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": "abc123",
        "host": "chise",
        "config": "nixos",
        "threshold_percent": 200,
        "measurements": {
            name: {"avg_ms": average, "max_allowed_ms": ceiling}
            for name, (average, ceiling) in measurements.items()
        },
    }


def _compare(tmp_path, baseline: dict, csv_body: str | None) -> bool:
    baseline_file = tmp_path / "baseline-desktop.json"
    baseline_file.write_text(json.dumps(baseline))
    results_file = tmp_path / "desktop-times.csv"
    if csv_body is not None:
        results_file.write_text(CSV_ROWS + csv_body)

    with patch.object(benchmark_desktop, "BASELINE_PATH", baseline_file):
        return benchmark_desktop.compare_latest_to_baseline(results_file)


class TestCompareLatestToBaseline:
    def test_passes_when_every_tracked_component_stays_under_its_ceiling(
        self, tmp_path
    ):
        passed = _compare(
            tmp_path,
            _tracked_baseline(tmux=(20.0, 40.0)),
            "2026-01-01,tmux,30.0,25.0,35.0,5\n",
        )
        assert passed is True

    def test_fails_on_a_component_over_its_ceiling(self, tmp_path, capsys):
        passed = _compare(
            tmp_path,
            _tracked_baseline(tmux=(20.0, 40.0)),
            "2026-01-01,tmux,90.0,80.0,95.0,5\n",
        )

        assert passed is False
        report = capsys.readouterr().out
        assert "SLOWER" in report
        assert "tmux" in report

    def test_reads_the_latest_row_for_a_component(self, tmp_path):
        passed = _compare(
            tmp_path,
            _tracked_baseline(tmux=(20.0, 40.0)),
            "2026-01-01,tmux,10.0,10.0,10.0,5\n2026-01-02,tmux,90.0,90.0,90.0,5\n",
        )
        assert passed is False

    def test_fails_when_a_tracked_component_was_never_measured(self, tmp_path, capsys):
        passed = _compare(
            tmp_path,
            _tracked_baseline(tmux=(20.0, 40.0), wezterm=(50.0, 100.0)),
            "2026-01-01,tmux,30.0,25.0,35.0,5\n",
        )

        assert passed is False
        report = capsys.readouterr().out
        assert "MISSING" in report
        assert "wezterm" in report

    def test_fails_when_the_results_csv_does_not_exist(self, tmp_path, capsys):
        passed = _compare(tmp_path, _tracked_baseline(tmux=(20.0, 40.0)), None)

        assert passed is False
        report = capsys.readouterr().out
        assert "no measured results" in report

    def test_never_creates_the_results_csv_it_reads(self, tmp_path):
        _compare(tmp_path, _tracked_baseline(tmux=(20.0, 40.0)), None)
        assert not (tmp_path / "desktop-times.csv").exists()

    def test_fails_when_the_csv_holds_no_measurements_at_all(self, tmp_path, capsys):
        passed = _compare(tmp_path, _tracked_baseline(tmux=(20.0, 40.0)), "")

        assert passed is False
        assert "MISSING" in capsys.readouterr().out

    def test_fails_before_comparing_when_the_tracked_baseline_is_invalid(
        self, tmp_path, capsys
    ):
        baseline = _tracked_baseline(tmux=(20.0, 40.0))
        del baseline["host"]

        passed = _compare(tmp_path, baseline, "2026-01-01,tmux,30.0,25.0,35.0,5\n")

        assert passed is False
        report = capsys.readouterr().out
        assert "Baseline has no recorded host." in report

    def test_fails_on_a_stale_baseline_that_check_baseline_would_accept(
        self, tmp_path, capsys
    ):
        baseline = _tracked_baseline(tmux=(20.0, 40.0))
        stale = datetime.now(timezone.utc) - timedelta(days=200)
        baseline["generated_at"] = stale.isoformat(timespec="seconds")

        passed = _compare(tmp_path, baseline, "2026-01-01,tmux,30.0,25.0,35.0,5\n")

        assert passed is False
        report = capsys.readouterr().out
        assert "200 days old" in report
        assert benchmark_desktop.SAVE_BASELINE_COMMAND in report


class TestCompareLatestExitStatus:
    def _run_main(self, comparison_passed: bool) -> int:
        with (
            patch("benchmark_desktop.sys.argv", ["cmd", "--compare-latest"]),
            patch(
                "benchmark_desktop.compare_latest_to_baseline",
                return_value=comparison_passed,
            ),
            patch("benchmark_desktop.ensure_results_file_exists") as mock_ensure,
        ):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_desktop.main()
            mock_ensure.assert_not_called()
            return exit_info.value.code

    def test_exits_zero_when_the_comparison_passes(self):
        assert self._run_main(True) == 0

    def test_exits_one_when_the_comparison_fails(self):
        assert self._run_main(False) == 1
