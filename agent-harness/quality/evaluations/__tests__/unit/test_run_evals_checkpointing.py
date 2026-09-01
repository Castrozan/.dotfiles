import json
import tempfile
from pathlib import Path

from run_evals_baseline_incremental import BaselineCheckpoint
from run_evals_test_runner import TestResult


def test_baseline_checkpoint_writes_each_result_immediately():
    profile = {"subject": {"harness": "codex"}, "judge": {"harness": "codex"}}
    fingerprints = {"communication::first": "first-fingerprint"}
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "baseline.json"
        checkpoint = BaselineCheckpoint(profile, fingerprints, path=path)
        checkpoint.record(
            TestResult(
                name="first",
                passed=True,
                duration=0.0,
                output="answer",
                assertions_failed=[],
                category="communication",
            )
        )

        baseline = json.loads(path.read_text())

    assert baseline["total_tests"] == 1
    assert (
        baseline["categories"]["communication"]["tests"][0]["fingerprint"]
        == "first-fingerprint"
    )


def test_explicit_full_refresh_does_not_carry_prior_usage(tmp_path):
    path = tmp_path / "baseline.json"
    profile = {"subject": {"harness": "codex"}, "judge": {"harness": "codex"}}
    path.write_text(
        json.dumps(
            {
                "execution_profile": profile,
                "token_usage": {"subject": {"codex": {"invocations": 50}}},
            }
        )
    )

    checkpoint = BaselineCheckpoint(
        profile,
        {"communication::first": "first-fingerprint"},
        path=path,
        reset_test_keys={"communication::first"},
    )

    assert checkpoint.initial_usage == {}


def test_filtered_full_refresh_preserves_unselected_results(tmp_path):
    path = tmp_path / "baseline.json"
    profile = {"subject": {"harness": "codex"}, "judge": {"harness": "codex"}}
    fingerprints = {
        "communication::first": "first-fingerprint",
        "other::second": "second-fingerprint",
    }
    path.write_text(
        json.dumps(
            {
                "execution_profile": profile,
                "categories": {
                    "communication": {
                        "tests": [
                            {
                                "name": "first",
                                "passed": False,
                                "fingerprint": "first-fingerprint",
                                "generated_at": "2026-08-31T00:00:00+00:00",
                            }
                        ]
                    },
                    "other": {
                        "tests": [
                            {
                                "name": "second",
                                "passed": True,
                                "fingerprint": "second-fingerprint",
                                "generated_at": "2026-08-31T00:00:00+00:00",
                            }
                        ]
                    },
                },
            }
        )
    )
    checkpoint = BaselineCheckpoint(
        profile,
        fingerprints,
        path=path,
        reset_test_keys={"communication::first"},
    )

    checkpoint.record(
        TestResult(
            name="first",
            passed=True,
            duration=0.0,
            output="answer",
            assertions_failed=[],
            category="communication",
        )
    )

    baseline = json.loads(path.read_text())
    assert baseline["categories"]["other"]["tests"][0]["name"] == "second"


def test_invocation_errors_are_not_checkpointed(tmp_path):
    path = tmp_path / "baseline.json"
    profile = {"subject": {"harness": "codex"}, "judge": {"harness": "codex"}}
    checkpoint = BaselineCheckpoint(
        profile,
        {"communication::provider_limit": "provider-limit-fingerprint"},
        path=path,
    )

    checkpoint.record(
        TestResult(
            name="provider_limit",
            passed=False,
            duration=0.0,
            output="",
            assertions_failed=[],
            error="session limit reached",
            category="communication",
        )
    )

    assert not path.exists()
