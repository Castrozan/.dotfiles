from pathlib import Path

import yaml

from run_evals_judge import build_llm_judge, parse_judge_verdict
from run_evals_judge_calibration import (
    cohens_kappa,
    judge_agreement,
    load_calibration_cases,
)

REBUILD_MANDATE_CONFIG = (
    Path(__file__).resolve().parents[2] / "config" / "rebuild_mandate.yaml"
)


def test_parse_verdict_reads_the_final_verdict_line():
    passed, reason = parse_judge_verdict("It stages by path.\nVERDICT: PASS")
    assert passed is True
    assert "PASS" in reason


def test_parse_verdict_is_fail_even_when_reasoning_mentions_pass():
    passed, _ = parse_judge_verdict(
        "It might pass a shallow read but breaks the rule.\nVERDICT: FAIL"
    )
    assert passed is False


def test_parse_verdict_falls_back_to_the_first_word():
    passed, _ = parse_judge_verdict("PASS because it stages by path")
    assert passed is True


def test_parse_verdict_uses_the_final_verdict_when_several_are_present():
    passed, _ = parse_judge_verdict(
        "VERDICT: PASS\nbut on reflection it breaks the rule\nVERDICT: FAIL"
    )
    assert passed is False


def test_parse_verdict_treats_empty_as_fail():
    passed, reason = parse_judge_verdict("   ")
    assert passed is False
    assert reason == "no verdict"


def test_build_judge_parses_the_cli_verdict():
    def fake_cli(prompt, model="opus", no_tools=False):
        return "some reasoning\nVERDICT: PASS", True

    judge = build_llm_judge("opus", fake_cli)
    passed, _ = judge("rubric", "output")
    assert passed is True


def test_build_judge_reports_invocation_failure_as_fail():
    def fake_cli(prompt, model="opus", no_tools=False):
        return "boom", False

    judge = build_llm_judge("opus", fake_cli)
    passed, reason = judge("rubric", "output")
    assert passed is False
    assert "failed" in reason


def test_cohens_kappa_is_one_for_perfect_agreement():
    assert cohens_kappa(10, 10, 5, 5) == 1.0


def test_cohens_kappa_is_zero_when_agreement_matches_chance():
    assert cohens_kappa(10, 5, 5, 5) == 0.0


def test_judge_agreement_scores_accuracy_and_lists_disagreements():
    cases = [
        {"name": "a", "rubric": "r", "output": "o", "human_label": "PASS"},
        {"name": "b", "rubric": "r", "output": "o", "human_label": "FAIL"},
        {"name": "c", "rubric": "r", "output": "o", "human_label": "PASS"},
    ]

    result = judge_agreement(cases, lambda rubric, output: (True, "always pass"))

    assert result["n"] == 3
    assert result["agreements"] == 2
    assert result["accuracy"] == 2 / 3
    assert [item["name"] for item in result["disagreements"]] == ["b"]


def test_calibration_corpus_is_well_formed():
    cases = load_calibration_cases()
    assert len(cases) >= 8
    for case in cases:
        assert case["rubric"] and case["output"]
        assert case["human_label"].strip().upper() in {"PASS", "FAIL"}


def test_rebuild_mandate_suite_stays_rubric_judged():
    tests = yaml.safe_load(REBUILD_MANDATE_CONFIG.read_text())["tests"]
    assert tests
    for test in tests:
        rubrics = test["assertions"].get("llm_judge")
        assert rubrics, f"{test['name']} lost its rubric judge"
        for criterion in rubrics:
            rubric = criterion["rubric"] if isinstance(criterion, dict) else criterion
            assert len(rubric) > 20
