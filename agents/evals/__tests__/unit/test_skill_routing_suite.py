from pathlib import Path

import yaml

SKILL_ROUTING_CONFIG = (
    Path(__file__).resolve().parents[2] / "config" / "skill_routing.yaml"
)


def test_skill_routing_grades_by_exact_match_not_substring():
    tests = yaml.safe_load(SKILL_ROUTING_CONFIG.read_text())["tests"]
    assert tests
    for test in tests:
        assertions = test["assertions"]
        assert "output_equals" in assertions, (
            f"{test['name']} lost its exact-match grading"
        )
        assert "output_contains_any" not in assertions, (
            f"{test['name']} still grades by substring"
        )
        assert "output_contains" not in assertions
        assert "output_not_contains" not in assertions
        assert len(assertions["output_equals"]) >= 1
