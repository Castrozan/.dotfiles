from pathlib import Path

import yaml

RECOVERY_SUITE = (
    Path(__file__).resolve().parents[4]
    / "agent-instructions/skills/humanize/__tests__/evals/reader_recovery.yaml"
)
REQUIRED_FAILURE_MODES = {
    "task_outcome",
    "missing_context",
    "concept_density",
    "verbosity",
    "representation",
    "channel_constraint",
    "control",
}
INTERACTIVE_POLICY = (
    "agent-harness/agent-instructions/skills/humanize/interactive-communication.md"
)


def recovery_tests():
    return yaml.safe_load(RECOVERY_SUITE.read_text())["tests"]


def test_recovery_suite_covers_observed_failures_and_false_positive_controls():
    tests = recovery_tests()
    assert len(tests) >= 20
    modes = {test["failure_mode"] for test in tests}
    assert modes == REQUIRED_FAILURE_MODES
    for mode in REQUIRED_FAILURE_MODES - {"control"}:
        assert sum(test["failure_mode"] == mode for test in tests) >= 2
    assert sum(test["failure_mode"] == "control" for test in tests) >= 3


def test_recovery_suite_grades_behavior_with_the_full_chat_policy():
    for test in recovery_tests():
        assert test["assertions"].get("llm_judge")
        assert INTERACTIVE_POLICY in test["extra_skill_paths"]
        assert test["no_tools"] is True
