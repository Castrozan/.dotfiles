import json
from datetime import datetime, timedelta, timezone

import benchmark_baseline

SAVE_COMMAND = "benchmark-rebuild --save-baseline"


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


class TestGeneratedAtValidation:
    def test_reports_a_missing_timestamp_without_raising(self, tmp_path):
        document = _document()
        del document["generated_at"]
        validation = _validate(_write(tmp_path, document))
        assert validation.age_days is None
        assert any("generated_at" in failure for failure in validation.failures)

    def test_reports_an_unparseable_timestamp_without_raising(self, tmp_path):
        validation = _validate(
            _write(tmp_path, _document(generated_at="not-a-timestamp"))
        )
        assert validation.age_days is None
        assert any("generated_at" in failure for failure in validation.failures)

    def test_reports_a_non_string_timestamp_without_raising(self, tmp_path):
        validation = _validate(_write(tmp_path, _document(generated_at=17)))
        assert validation.age_days is None
        assert any("generated_at" in failure for failure in validation.failures)

    def test_reports_a_stale_baseline(self, tmp_path):
        stale = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        validation = _validate(_write(tmp_path, _document(generated_at=stale)))
        assert validation.age_days == 45
        assert "45 days old" in validation.failures[0]
        assert SAVE_COMMAND in validation.failures[0]
