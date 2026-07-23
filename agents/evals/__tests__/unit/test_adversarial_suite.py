from pathlib import Path

import yaml

from run_evals_hook_test_runner import evaluate_hook_test

ADVERSARIAL_CONFIG = Path(__file__).resolve().parents[2] / "config" / "adversarial.yaml"


def _adversarial_tests():
    return yaml.safe_load(ADVERSARIAL_CONFIG.read_text())["tests"]


def test_adversarial_config_is_all_deterministic_hook_tests():
    tests = _adversarial_tests()
    assert tests
    assert all(test.get("type") == "hook_test" for test in tests)


def test_every_adversarial_defense_holds():
    failures = {}
    for test in _adversarial_tests():
        result = evaluate_hook_test(test)
        if result:
            failures[test["name"]] = result
    assert not failures, failures
