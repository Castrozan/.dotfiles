from pathlib import Path

import pytest
import yaml
from hypothesis import example, given
from hypothesis import strategies as st

from runner.judging.run_evals_judge import (
    JudgeInvocationError,
    build_llm_judge,
    parse_judge_verdict,
)
from runner.judging.run_evals_judge_calibration import (
    CALIBRATION_PATH,
    cohens_kappa,
    load_calibration_cases,
)

RECORDED_KAPPA_FLOOR = 0.7

REBUILD_MANDATE_SUITE = (
    Path(__file__).resolve().parents[3] / "evals/rebuild_mandate.yaml"
)

REASONING_WORDS = ["PASS", "FAIL", "pass", "fail", "might", "breaks", "rule"]
REASONING_LINES = st.lists(
    st.lists(st.sampled_from(REASONING_WORDS), min_size=1, max_size=6).map(" ".join),
    max_size=4,
)


@st.composite
def judge_output_with_expected_verdict(draw):
    reasoning_lines = draw(REASONING_LINES)
    final_verdict = draw(st.sampled_from(["PASS", "FAIL"]))
    raw_verdict = "\n".join([*reasoning_lines, f"VERDICT: {final_verdict}"])
    return raw_verdict, final_verdict == "PASS"


def test_parse_verdict_reads_the_final_verdict_line():
    passed, reason = parse_judge_verdict("It stages by path.\nVERDICT: PASS")
    assert passed is True
    assert reason == "It stages by path.\nVERDICT: PASS"


@given(judge_output_with_expected_verdict())
@example(("It might pass a shallow read but breaks the rule.\nVERDICT: FAIL", False))
@example(("VERDICT: PASS because no FAIL condition applies", True))
@example(("VERDICT: PASS\nbut on reflection it breaks the rule\nVERDICT: FAIL", False))
def test_parse_verdict_follows_the_final_verdict_whatever_the_reasoning_says(
    judge_output,
):
    raw_verdict, expected_passed = judge_output
    passed, _ = parse_judge_verdict(raw_verdict)
    assert passed is expected_passed


def test_parse_verdict_falls_back_to_the_first_word():
    passed, _ = parse_judge_verdict("PASS because it stages by path")
    assert passed is True


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


def test_a_judge_without_a_request_is_never_shown_an_empty_one():
    prompts = []

    def fake_cli(prompt, model="opus", no_tools=False):
        prompts.append(prompt)
        return "VERDICT: PASS", True

    build_llm_judge("opus", fake_cli)("rubric", "output")
    build_llm_judge("opus", fake_cli, subject_prompt="Fix the bug")("rubric", "output")

    assert "Original request" not in prompts[0]
    assert "Original request:\nFix the bug" in prompts[1]


def test_build_judge_reports_invocation_failure_as_infrastructure_error():
    def fake_cli(prompt, model="opus", no_tools=False):
        return "boom", False

    judge = build_llm_judge("opus", fake_cli)
    with pytest.raises(JudgeInvocationError, match="invocation failed"):
        judge("rubric", "output")


def test_cohens_kappa_is_one_for_perfect_agreement():
    assert cohens_kappa(10, 10, 5, 5) == 1.0


def test_cohens_kappa_is_zero_when_agreement_matches_chance():
    assert cohens_kappa(10, 5, 5, 5) == 0.0


def test_calibration_corpus_is_well_formed():
    cases = load_calibration_cases()
    assert len(cases) >= 8
    for case in cases:
        assert case["rubric"] and case["output"]
        assert case["rubric_family"]
        assert case["human_label"].strip().upper() in {"PASS", "FAIL"}


def test_calibration_corpus_covers_the_conversion_rubric_families_with_both_labels():
    cases = load_calibration_cases()
    assert len(cases) >= 20
    distinct_rubrics = {case["rubric"] for case in cases}
    assert len(distinct_rubrics) >= 10
    labels = {case["human_label"].strip().upper() for case in cases}
    assert labels == {"PASS", "FAIL"}
    for rubric in distinct_rubrics:
        rubric_labels = {
            case["human_label"].strip().upper()
            for case in cases
            if case["rubric"] == rubric
        }
        assert rubric_labels == {"PASS", "FAIL"}, rubric


def test_recorded_agreement_stays_above_the_kappa_floor_and_matches_the_corpus():
    corpus = yaml.safe_load(CALIBRATION_PATH.read_text())
    recorded = corpus["recorded_agreement"]
    assert recorded["cohens_kappa"] >= RECORDED_KAPPA_FLOOR
    assert recorded["cases"] == len(corpus["cases"])
    assert recorded["balanced_accuracy"] >= 0.8
    assert recorded["failed_case_recall"] >= 0.8


def test_rebuild_mandate_suite_stays_rubric_judged():
    tests = yaml.safe_load(REBUILD_MANDATE_SUITE.read_text())["tests"]
    assert tests
    for test in tests:
        rubrics = test["assertions"].get("llm_judge")
        assert rubrics, f"{test['name']} lost its rubric judge"
        for criterion in rubrics:
            rubric = criterion["rubric"] if isinstance(criterion, dict) else criterion
            assert len(rubric) > 20
