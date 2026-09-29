from pathlib import Path

import yaml

ADVERSARIAL_SUITE = Path(__file__).resolve().parents[3] / "evals/adversarial.yaml"


def _adversarial_tests():
    return yaml.safe_load(ADVERSARIAL_SUITE.read_text())["tests"]


def test_adversarial_suite_is_all_deterministic_hook_tests():
    tests = _adversarial_tests()
    assert tests
    assert all(test.get("type") == "hook_test" for test in tests)
