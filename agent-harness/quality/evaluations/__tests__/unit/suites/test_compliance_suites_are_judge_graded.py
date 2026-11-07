from evaluation_suite_support import load_suite_cases

JUDGE_GRADED_COMPLIANCE_SUITES = [
    "instruction_compliance",
    "workflow_compliance",
    "rebuild_mandate",
    "delegation",
    "core_rules",
]
MINIMUM_RUBRIC_CHARACTERS = 20


def test_compliance_suites_grade_every_case_by_rubric():
    for suite_name in JUDGE_GRADED_COMPLIANCE_SUITES:
        cases = load_suite_cases(suite_name)
        assert cases, suite_name
        for case in cases:
            rubrics = case["assercoes"].get("juiz")
            assert rubrics, f"{suite_name}:{case['nome']} lost its rubric judge"
            for rubric in rubrics:
                assert len(rubric) > MINIMUM_RUBRIC_CHARACTERS
            assert "contem" not in case["assercoes"], (
                f"{suite_name}:{case['nome']} still grades by substring"
            )
