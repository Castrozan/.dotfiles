import tempfile
from pathlib import Path

from run_evals_impact import affected_test_keys, evaluation_test_fingerprints


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


def test_instruction_change_only_invalidates_tests_that_reference_it():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        create_instruction(root, "first", "first policy")
        create_instruction(root, "second", "second policy")
        config = evaluation_config()
        original = evaluation_test_fingerprints(config, root)

        create_instruction(root, "first", "changed first policy")
        changed = evaluation_test_fingerprints(config, root)

        assert changed["communication::first"] != original["communication::first"]
        assert changed["communication::second"] == original["communication::second"]


def test_instruction_frontmatter_does_not_invalidate_behavioral_evidence():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        config = evaluation_config()
        create_instruction(root, "first", "---\nname: first\n---\nfirst policy")
        create_instruction(root, "second", "second policy")
        original = evaluation_test_fingerprints(config, root)

        create_instruction(root, "first", "---\nname: renamed\n---\nfirst policy")

        assert evaluation_test_fingerprints(config, root) == original


def test_execution_tuning_does_not_invalidate_independent_test_evidence():
    config = evaluation_config()
    original = evaluation_test_fingerprints(config)

    config["tests"]["communication"][0]["models"] = {"codex": "different"}
    config["settings"]["timeout_seconds"] = 300

    assert evaluation_test_fingerprints(config) == original


def test_instruction_loading_order_invalidates_the_referencing_test():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        create_instruction(root, "first", "first policy")
        create_instruction(root, "second", "second policy")
        config = evaluation_config()
        test = config["tests"]["communication"][0]
        test["extra_skill_paths"] = [
            "agent-harness/agent-instructions/skills/second/SKILL.md"
        ]
        original = evaluation_test_fingerprints(config, root)

        test["skill_path"], test["extra_skill_paths"][0] = (
            test["extra_skill_paths"][0],
            test["skill_path"],
        )

        assert evaluation_test_fingerprints(config, root) != original


def test_affected_selection_returns_only_missing_or_stale_tests():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        create_instruction(root, "first", "first policy")
        create_instruction(root, "second", "second policy")
        config = evaluation_config()
        fingerprints = evaluation_test_fingerprints(config, root)
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

        assert affected_test_keys(config, baseline, root) == {"communication::second"}


def test_execution_profile_change_preserves_independent_test_evidence():
    config = evaluation_config()
    fingerprints = evaluation_test_fingerprints(config)
    generated_at = "2026-08-31T00:00:00+00:00"
    baseline = {
        "execution_profile": {"subject": {}},
        "categories": {
            "communication": {
                "tests": [
                    {
                        "name": name,
                        "passed": True,
                        "fingerprint": fingerprint,
                        "generated_at": generated_at,
                    }
                    for name, fingerprint in (
                        ("first", fingerprints["communication::first"]),
                        ("second", fingerprints["communication::second"]),
                    )
                ]
            }
        },
    }

    assert affected_test_keys(config, baseline) == set()
