from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

JUDGE_GRADED_COMPLIANCE_SUITES = [
    "instruction_compliance.yaml",
    "workflow_compliance.yaml",
    "delegation.yaml",
    "core_rules.yaml",
]


def test_converted_compliance_suites_grade_every_test_by_rubric():
    for suite_name in JUDGE_GRADED_COMPLIANCE_SUITES:
        tests = yaml.safe_load((CONFIG_DIR / suite_name).read_text())["tests"]
        assert tests, suite_name
        for test in tests:
            rubrics = test["assertions"].get("llm_judge")
            assert rubrics, f"{suite_name}:{test['name']} lost its rubric judge"
            for criterion in rubrics:
                rubric = (
                    criterion["rubric"] if isinstance(criterion, dict) else criterion
                )
                assert len(rubric) > 20
            assert "output_contains_any" not in test["assertions"], (
                f"{suite_name}:{test['name']} still grades by substring"
            )
            assert "output_contains" not in test["assertions"], (
                f"{suite_name}:{test['name']} still grades by substring"
            )
