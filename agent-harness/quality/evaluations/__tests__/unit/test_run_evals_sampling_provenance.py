from collections import namedtuple

import run_evals_sampling
from run_evals_execution_profile import execution_profile_identifier
from run_evals_sampling import aggregate_repeated_runs, build_epoch_enriched_baseline

FakeResult = namedtuple("FakeResult", ["name", "passed", "category"])
EXECUTION_PROFILE = {
    "subject": {"harness": "codex", "model": "gpt-5.6-sol"},
    "judge": {"harness": "codex", "model": "gpt-5.6-luna"},
}


def test_full_repeated_baseline_records_coverage_and_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals_sampling, "BASELINE_PATH", tmp_path / "baseline.json")
    per_test = aggregate_repeated_runs([[FakeResult("case", True, "communication")]])

    baseline = build_epoch_enriched_baseline(
        per_test,
        1,
        "deadbeef",
        "2026-09-01T00:00:00+00:00",
        EXECUTION_PROFILE,
        {},
        {"communication::case": "case-sha"},
    )

    profile_id = execution_profile_identifier(EXECUTION_PROFILE)
    assert baseline["minimum_current_evidence"] == 1
    assert baseline["oldest_evidence_at"] == baseline["generated_at"]
    assert baseline["execution_profiles"] == {profile_id: EXECUTION_PROFILE}
    assert baseline["categories"]["communication"]["tests"][0] == {
        "name": "case",
        "passed": True,
        "passes": 1,
        "samples": 1,
        "lower": 0.2065,
        "upper": 1.0,
        "fingerprint": "case-sha",
        "generated_at": "2026-09-01T00:00:00+00:00",
        "execution_profile_id": profile_id,
        "run_source": {"kind": "repeated_sampling", "git_commit": "deadbeef"},
    }
