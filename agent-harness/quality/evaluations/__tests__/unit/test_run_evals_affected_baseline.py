import tempfile
from pathlib import Path

from run_evals_baseline_incremental import merge_baseline_results
from run_evals_impact import affected_test_keys, evaluation_test_fingerprints
from run_evals_test_runner import TestResult


EXECUTION_PROFILE = {
    "subject": {"harness": "codex", "model": "gpt-5.6-sol", "reasoning_effort": "high"},
    "judge": {"harness": "codex", "model": "gpt-5.6-luna", "reasoning_effort": "low"},
}


def evaluation_config():
    return {
        "settings": {"timeout_seconds": 120},
        "tests": {
            "communication": [
                {
                    "name": "first",
                    "prompt": "first prompt",
                    "skill_path": "agent-harness/agent-instructions/skills/first/SKILL.md",
                },
                {
                    "name": "second",
                    "prompt": "second prompt",
                    "skill_path": "agent-harness/agent-instructions/skills/second/SKILL.md",
                },
            ]
        },
    }


def create_instruction(root: Path, name: str, content: str):
    path = root / f"agent-harness/agent-instructions/skills/{name}/SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def result(name: str, passed: bool):
    return TestResult(
        name=name,
        passed=passed,
        duration=0.0,
        output="",
        assertions_failed=[] if passed else ["failed"],
        category="communication",
    )


def test_instruction_change_only_invalidates_tests_that_reference_it():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        create_instruction(root, "first", "first policy")
        create_instruction(root, "second", "second policy")
        config = evaluation_config()
        original = evaluation_test_fingerprints(config, EXECUTION_PROFILE, root)

        create_instruction(root, "first", "changed first policy")
        changed = evaluation_test_fingerprints(config, EXECUTION_PROFILE, root)

        assert changed["communication::first"] != original["communication::first"]
        assert changed["communication::second"] == original["communication::second"]


def test_instruction_frontmatter_does_not_invalidate_behavioral_evidence():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        config = evaluation_config()
        create_instruction(root, "first", "---\nname: first\n---\nfirst policy")
        create_instruction(root, "second", "second policy")
        original = evaluation_test_fingerprints(config, EXECUTION_PROFILE, root)

        create_instruction(root, "first", "---\nname: renamed\n---\nfirst policy")

        assert evaluation_test_fingerprints(config, EXECUTION_PROFILE, root) == original


def test_affected_selection_returns_only_missing_or_stale_tests():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        create_instruction(root, "first", "first policy")
        create_instruction(root, "second", "second policy")
        config = evaluation_config()
        fingerprints = evaluation_test_fingerprints(config, EXECUTION_PROFILE, root)
        baseline = {
            "execution_profile": EXECUTION_PROFILE,
            "categories": {
                "communication": {
                    "tests": [
                        {
                            "name": "first",
                            "passed": True,
                            "fingerprint": fingerprints["communication::first"],
                            "generated_at": "2026-08-31T00:00:00+00:00",
                        }
                    ]
                }
            },
        }

        assert affected_test_keys(config, baseline, EXECUTION_PROFILE, root) == {
            "communication::second"
        }


def test_execution_profile_change_invalidates_every_test():
    config = evaluation_config()
    baseline = {"execution_profile": {"subject": {}}, "categories": {}}

    assert affected_test_keys(config, baseline, EXECUTION_PROFILE) == {
        "communication::first",
        "communication::second",
    }


def test_per_test_merge_preserves_fresh_results_and_prunes_obsolete_tests():
    fingerprints = {
        "communication::first": "first-fingerprint",
        "communication::second": "second-fingerprint",
    }
    baseline = {
        "execution_profile": EXECUTION_PROFILE,
        "categories": {
            "communication": {
                "passed": 1,
                "failed": 1,
                "tests": [
                    {
                        "name": "first",
                        "passed": True,
                        "fingerprint": "first-fingerprint",
                        "generated_at": "2026-08-30T00:00:00+00:00",
                    },
                    {
                        "name": "stale",
                        "passed": False,
                        "fingerprint": "stale-fingerprint",
                        "generated_at": "2026-08-30T00:00:00+00:00",
                    },
                ],
            },
            "obsolete": {
                "passed": 1,
                "failed": 0,
                "tests": [
                    {
                        "name": "gone",
                        "passed": True,
                        "fingerprint": "gone-fingerprint",
                        "generated_at": "2026-08-30T00:00:00+00:00",
                    }
                ],
            },
        },
    }

    merged = merge_baseline_results(
        baseline,
        [result("second", False)],
        EXECUTION_PROFILE,
        {"subject": {"codex": {"invocations": 1}}},
        fingerprints,
        "2026-08-31T00:00:00+00:00",
    )

    assert set(merged["categories"]) == {"communication"}
    assert merged["categories"]["communication"]["tests"] == [
        {
            "name": "first",
            "passed": True,
            "fingerprint": "first-fingerprint",
            "generated_at": "2026-08-30T00:00:00+00:00",
        },
        {
            "name": "second",
            "passed": False,
            "fingerprint": "second-fingerprint",
            "generated_at": "2026-08-31T00:00:00+00:00",
        },
    ]
    assert merged["total_passed"] == 1
    assert merged["total_tests"] == 2
    assert merged["generated_at"] == "2026-08-30T00:00:00+00:00"
