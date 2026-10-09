from runner.baseline.run_evals_baseline_reporting import (
    BaselineCheckSummary,
    print_baseline_summary,
)


def test_pending_evidence_identifies_stale_and_missing_current_fingerprints(capsys):
    summary = BaselineCheckSummary(
        baseline={"generated_at": "2026-10-09", "total_passed": 1, "total_tests": 3},
        age_days=0,
        current_passed=1,
        current_total=1,
        evidence_status={
            "fresh": {"suite::fresh"},
            "stale": {"suite::stale"},
            "missing": {"suite::missing"},
        },
        current_test_fingerprints={
            "suite::fresh": "fresh-hash",
            "suite::stale": "stale-hash",
            "suite::missing": "missing-hash",
        },
        compliance_passed=0,
        compliance_total=0,
        previous_pass_rate=None,
        materialized_pass_rate=1 / 3,
    )
    print_baseline_summary(summary)
    output = capsys.readouterr().out
    assert "Pending evidence: 1 stale, 1 missing" in output
    assert "Stale evidence: suite::stale (current fingerprint stale-hash)" in output
    assert (
        "Missing evidence: suite::missing (current fingerprint missing-hash)" in output
    )
    assert "fresh-hash" not in output
