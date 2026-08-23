import json
from datetime import datetime, timezone
from unittest.mock import patch

import benchmark_desktop
import benchmark_rebuild
from benchmark_baseline import (
    BaselineValidation,
    compare_measured_values,
    with_freshness_required,
)
from benchmark_report import baseline_report_lines

SAVE_COMMAND = "benchmark-desktop --save-baseline"
GENERATED_AT = datetime.now(timezone.utc).isoformat(timespec="seconds")


def _provenance() -> dict:
    return {
        "generated_at": GENERATED_AT,
        "git_commit": "abc1234",
        "host": "kira",
        "config": "darwin",
        "threshold_percent": 150,
    }


def _validation(failures: list[str], age_days: int | None = 3) -> BaselineValidation:
    return BaselineValidation(_provenance(), age_days, failures)


def _header_lines(module, document: dict, tmp_path, capsys) -> list[str]:
    baseline_file = tmp_path / f"{module.__name__}.json"
    baseline_file.write_text(json.dumps(document))
    with patch.object(module, "BASELINE_PATH", baseline_file):
        module.check_baseline(False)
    return capsys.readouterr().out.splitlines()[:8]


class TestFreshnessRequirement:
    def test_accepts_an_age_inside_the_window(self):
        gated = with_freshness_required(_validation([], age_days=0), SAVE_COMMAND)
        assert gated.failures == []

    def test_rejects_an_age_past_the_window(self):
        gated = with_freshness_required(_validation([], age_days=45), SAVE_COMMAND)
        assert "45 days old" in gated.failures[0]
        assert SAVE_COMMAND in gated.failures[0]

    def test_rejects_an_unusable_timestamp(self):
        gated = with_freshness_required(_validation([], age_days=None), SAVE_COMMAND)
        assert "generated_at" in gated.failures[0]
        assert SAVE_COMMAND in gated.failures[0]

    def test_keeps_the_failures_the_validation_already_carried(self):
        gated = with_freshness_required(_validation(["structural"], 45), SAVE_COMMAND)
        assert gated.failures[0] == "structural"
        assert len(gated.failures) == 2


class TestBaselineReportLines:
    def test_renders_the_provenance_block_under_the_title(self):
        lines = baseline_report_lines("A TITLE", _validation([]))
        assert lines[1] == "A TITLE"
        assert lines[0] == lines[2] == "=" * 60
        assert lines[3] == f"  Generated: {GENERATED_AT}"
        assert lines[4] == "  Age: 3 days"
        assert lines[5] == "  Commit: abc1234"
        assert lines[6] == "  Host: kira/darwin"
        assert lines[7] == "  Threshold: 150%"

    def test_renders_an_unknown_age_without_a_measured_age(self):
        lines = baseline_report_lines("A TITLE", _validation([], age_days=None))
        assert lines[4] == "  Age: unknown"

    def test_appends_every_failure_under_a_counted_heading(self):
        lines = baseline_report_lines("A TITLE", _validation(["first", "second"]))
        assert lines[-3] == "FAILED (2 issues):"
        assert lines[-2] == "  - first"
        assert lines[-1] == "  - second"

    def test_appends_no_heading_without_failures(self):
        assert len(baseline_report_lines("A TITLE", _validation([]))) == 8


class TestSharedHeaderAcrossCommands:
    def test_both_commands_render_the_same_provenance_block(self, tmp_path, capsys):
        desktop = _header_lines(
            benchmark_desktop,
            {
                **_provenance(),
                "measurements": {"tmux": {"avg_ms": 5, "max_allowed_ms": 9}},
            },
            tmp_path,
            capsys,
        )
        rebuild = _header_lines(
            benchmark_rebuild,
            {
                **_provenance(),
                "measurements": {
                    "eval": {"duration_seconds": 2.0, "max_allowed_seconds": 3.0}
                },
            },
            tmp_path,
            capsys,
        )

        assert desktop[0] == rebuild[0]
        assert desktop[2] == rebuild[2]
        assert desktop[3:8] == rebuild[3:8]
        assert desktop[1] != rebuild[1]


class TestCompareMeasuredValues:
    def _document(self, **measurements) -> dict:
        return {
            "measurements": {
                name: {"max_allowed_ms": ceiling}
                for name, ceiling in measurements.items()
            }
        }

    def test_reports_nothing_within_the_ceiling(self):
        comparison = compare_measured_values(
            self._document(comp=100), {"comp": 80.0}, "max_allowed_ms"
        )
        assert comparison.exceeded_names == []
        assert comparison.missing_names == []

    def test_names_a_measurement_over_its_ceiling(self):
        comparison = compare_measured_values(
            self._document(comp=100), {"comp": 150.0}, "max_allowed_ms"
        )
        assert comparison.exceeded_names == ["comp"]

    def test_names_measurements_that_were_never_taken(self):
        comparison = compare_measured_values(
            self._document(**{"comp-a": 100, "comp-b": 100}),
            {"comp-a": 80.0},
            "max_allowed_ms",
        )
        assert comparison.exceeded_names == []
        assert comparison.missing_names == ["comp-b"]

    def test_names_every_measurement_when_nothing_was_measured(self):
        comparison = compare_measured_values(
            self._document(comp=100), {}, "max_allowed_ms"
        )
        assert comparison.missing_names == ["comp"]

    def test_reads_the_ceiling_key_it_is_given(self):
        comparison = compare_measured_values(
            {"measurements": {"eval": {"max_allowed_seconds": 3.0}}},
            {"eval": 4.0},
            "max_allowed_seconds",
        )
        assert comparison.exceeded_names == ["eval"]
