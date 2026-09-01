import pytest

import run_evals_baseline_record
import run_evals_baseline_store


def test_repeated_baseline_write_preserves_the_previous_file_on_failure(
    tmp_path, monkeypatch
):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text('{"original":true}\n')
    monkeypatch.setattr(run_evals_baseline_record, "BASELINE_PATH", baseline_path)

    def fail_serialization(document, destination, indent):
        destination.write('{"partial":')
        raise RuntimeError("serialization failed")

    monkeypatch.setattr(run_evals_baseline_store.json, "dump", fail_serialization)

    with pytest.raises(RuntimeError, match="serialization failed"):
        run_evals_baseline_record.write_baseline(
            {
                "pass_rate": 1,
                "total_passed": 1,
                "total_tests": 1,
                "git_commit": "abc123",
            }
        )

    assert baseline_path.read_text() == '{"original":true}\n'
    assert list(tmp_path.iterdir()) == [baseline_path]
