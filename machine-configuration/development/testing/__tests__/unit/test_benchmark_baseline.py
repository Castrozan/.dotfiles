import json
from datetime import datetime, timedelta, timezone

import pytest

import benchmark_baseline

SAVE_COMMAND = "benchmark-rebuild --save-baseline"
MISSING = object()


def _fresh_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write(tmp_path, payload):
    baseline_path = tmp_path / "baseline.json"
    if isinstance(payload, str):
        baseline_path.write_text(payload)
    else:
        baseline_path.write_text(json.dumps(payload))
    return baseline_path


def _validate(baseline_path):
    return benchmark_baseline.validate_tracked_baseline(
        baseline_path, "duration_seconds", "max_allowed_seconds", SAVE_COMMAND
    )


def _document(generated_at=None) -> dict:
    return {
        "generated_at": generated_at
        if generated_at is not None
        else _fresh_timestamp(),
        "git_commit": "abc1234",
        "host": "kira",
        "config": "darwin",
        "threshold_percent": 150,
        "measurements": {"eval": {"duration_seconds": 2.0, "max_allowed_seconds": 3.0}},
    }


class TestWriteBaseline:
    def test_writes_indented_json_with_a_trailing_newline(self, tmp_path):
        baseline_path = tmp_path / "baseline.json"
        benchmark_baseline.write_baseline(baseline_path, {"threshold_percent": 150})
        content = baseline_path.read_text()
        assert content.endswith("}\n")
        assert json.loads(content)["threshold_percent"] == 150


class TestValidBaseline:
    def test_reports_no_failures_and_an_age(self, tmp_path):
        validation = _validate(_write(tmp_path, _document()))
        assert validation.failures == []
        assert validation.age_days == 0
        assert validation.document["threshold_percent"] == 150

    def test_treats_a_naive_timestamp_as_utc(self, tmp_path):
        naive = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        validation = _validate(_write(tmp_path, _document(generated_at=naive)))
        assert validation.failures == []
        assert validation.age_days == 0


class TestUnreadableBaseline:
    def test_reports_a_missing_file_without_raising(self, tmp_path):
        validation = _validate(tmp_path / "absent.json")
        assert len(validation.failures) == 1
        assert "No baseline file at" in validation.failures[0]
        assert SAVE_COMMAND in validation.failures[0]
        assert validation.document == {}
        assert validation.age_days is None

    def test_reports_malformed_json_without_raising(self, tmp_path):
        validation = _validate(_write(tmp_path, "{not json"))
        assert len(validation.failures) == 1
        assert "not readable JSON" in validation.failures[0]
        assert validation.document == {}

    def test_reports_a_non_object_root_without_raising(self, tmp_path):
        validation = _validate(_write(tmp_path, [1, 2, 3]))
        assert len(validation.failures) == 1
        assert "not a JSON object" in validation.failures[0]
        assert validation.document == {}


class TestGeneratedAtAge:
    def test_reports_no_age_for_a_missing_timestamp(self, tmp_path):
        document = _document()
        del document["generated_at"]
        validation = _validate(_write(tmp_path, document))
        assert validation.age_days is None
        assert validation.failures == []

    def test_reports_no_age_for_an_unparseable_timestamp(self, tmp_path):
        validation = _validate(
            _write(tmp_path, _document(generated_at="not-a-timestamp"))
        )
        assert validation.age_days is None
        assert validation.failures == []

    def test_reports_no_age_for_a_non_string_timestamp(self, tmp_path):
        validation = _validate(_write(tmp_path, _document(generated_at=17)))
        assert validation.age_days is None
        assert validation.failures == []

    def test_measures_a_stale_baseline_without_failing_it(self, tmp_path):
        stale = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        validation = _validate(_write(tmp_path, _document(generated_at=stale)))
        assert validation.age_days == 45
        assert validation.failures == []


def _with_field(document: dict, field: str, value) -> dict:
    if value is MISSING:
        del document[field]
    else:
        document[field] = value
    return document


class TestMetadataValidation:
    @pytest.mark.parametrize(
        "git_commit",
        [MISSING, None, "", "   ", 1234, ["abc1234"]],
        ids=["missing", "null", "empty", "blank", "number", "list"],
    )
    def test_rejects_an_unusable_git_commit(self, tmp_path, git_commit):
        document = _with_field(_document(), "git_commit", git_commit)
        validation = _validate(_write(tmp_path, document))
        assert validation.failures == ["Baseline has no recorded git_commit."]

    @pytest.mark.parametrize(
        "host",
        [MISSING, None, "", "   ", 1234, ["kira"]],
        ids=["missing", "null", "empty", "blank", "number", "list"],
    )
    def test_rejects_a_baseline_that_names_no_measuring_host(self, tmp_path, host):
        document = _with_field(_document(), "host", host)
        validation = _validate(_write(tmp_path, document))
        assert validation.failures == ["Baseline has no recorded host."]

    @pytest.mark.parametrize(
        "config",
        [MISSING, None, "", "   ", 1234, ["darwin"]],
        ids=["missing", "null", "empty", "blank", "number", "list"],
    )
    def test_rejects_a_baseline_that_names_no_configuration(self, tmp_path, config):
        document = _with_field(_document(), "config", config)
        validation = _validate(_write(tmp_path, document))
        assert validation.failures == ["Baseline has no recorded config."]

    def test_reports_every_missing_provenance_field_at_once(self, tmp_path):
        document = _document()
        del document["host"]
        del document["config"]
        validation = _validate(_write(tmp_path, document))
        assert validation.failures == [
            "Baseline has no recorded host.",
            "Baseline has no recorded config.",
        ]

    @pytest.mark.parametrize(
        ("threshold_percent", "expected_failure"),
        [
            (MISSING, "Baseline threshold_percent is not a number."),
            (None, "Baseline threshold_percent is not a number."),
            (True, "Baseline threshold_percent is not a number."),
            ("150", "Baseline threshold_percent is not a number."),
            (0, "Baseline threshold_percent must be greater than zero."),
            (-10, "Baseline threshold_percent must be greater than zero."),
        ],
        ids=["missing", "null", "boolean", "string", "zero", "negative"],
    )
    def test_rejects_an_unusable_threshold_percent(
        self, tmp_path, threshold_percent, expected_failure
    ):
        document = _with_field(_document(), "threshold_percent", threshold_percent)
        validation = _validate(_write(tmp_path, document))
        assert validation.failures == [expected_failure]

    def test_accepts_recorded_metadata(self, tmp_path):
        validation = _validate(_write(tmp_path, _document()))
        assert validation.failures == []
