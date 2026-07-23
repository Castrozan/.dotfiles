from pathlib import Path

import yaml

from run_evals_hook_test_runner import evaluate_hook_test, find_hook_script

ADVERSARIAL_SUITE = Path(__file__).resolve().parents[2] / "config" / "adversarial.yaml"


def load_adversarial_tests():
    return yaml.safe_load(ADVERSARIAL_SUITE.read_text())["tests"]


def test_the_adversarial_injection_axis_is_not_empty():
    tests = load_adversarial_tests()
    assert len(tests) >= 4, (
        "the adversarial injection axis lost coverage; it must keep exercising the "
        "guards that stop an injected instruction from rewriting the agent's own "
        "rules or mass-staging unrelated work"
    )


def test_the_adversarial_axis_keeps_both_a_blocking_case_and_a_benign_control():
    tests = load_adversarial_tests()
    blocking = [t for t in tests if t["assertions"].get("hook_blocks") is True]
    benign = [t for t in tests if t["assertions"].get("hook_blocks") is False]
    assert blocking, "no blocking case: the axis would pass even with every guard off"
    assert benign, (
        "no benign control: the axis would pass even if a guard blocked everything"
    )


def test_every_adversarial_hook_script_resolves():
    unresolved = [
        t["name"]
        for t in load_adversarial_tests()
        if find_hook_script(t["hook"]) is None
    ]
    assert not unresolved, f"adversarial tests name missing hook scripts: {unresolved}"


def test_every_adversarial_guard_still_behaves_as_asserted():
    failures = {}
    for test in load_adversarial_tests():
        hook_failures = evaluate_hook_test(test)
        if hook_failures:
            failures[test["name"]] = hook_failures
    assert not failures, f"adversarial guards regressed: {failures}"
