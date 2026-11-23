import re

import yaml

from instructions.instruction_surface_scanner import REPO_ROOT

EVALUATION_CONFIGURATION = (
    REPO_ROOT / "agent-harness" / "quality" / "evaluations" / "config.yaml"
)
EXECUTION_BUDGET = 156
MAXIMUM_JUDGE_CRITERIA = 2
JUSTIFICATION_CLAUSE = re.compile(
    r"\b(explains?|explaining|justif(?:y|ies|ying)|mentions why)\b", re.IGNORECASE
)

def configuration():
    return yaml.safe_load(EVALUATION_CONFIGURATION.read_text())


def measured_cases():
    return [
        (f"{suite['categoria']}/{case['nome']}", case)
        for pattern in configuration()["casos"]
        for suite_path in sorted(REPO_ROOT.glob(pattern))
        for suite in [yaml.safe_load(suite_path.read_text())]
        for case in suite["casos"]
        if not case.get("pendente")
    ]


def judge_criteria(case):
    assertions = case.get("assercoes", {})
    return [
        *assertions.get("juiz", []),
        *[entry["rubrica"] for entry in assertions.get("juiz_sobre_comando", [])],
    ]


def executions(case, executions_by_level):
    if case.get("tipo", "instrucao") not in ("instrucao", "instruction"):
        return 1
    return case.get("execucoes", executions_by_level[case["nivel"]])


def test_the_suite_fits_its_execution_budget():
    executions_by_level = configuration()["execucoes"]
    total = sum(executions(case, executions_by_level) for _, case in measured_cases())
    assert total <= EXECUTION_BUDGET, (
        f"a full measurement now takes {total} executions and the budget is "
        f"{EXECUTION_BUDGET}: remove a case that pays less or lower a level's "
        "executions, never raise the budget"
    )


def test_no_case_charges_more_than_two_judge_criteria():
    crowded = {
        label: len(judge_criteria(case))
        for label, case in measured_cases()
        if len(judge_criteria(case)) > MAXIMUM_JUDGE_CRITERIA
    }
    assert not crowded, (
        f"a case that charges several things fails on its weakest criterion: {crowded}"
    )


def test_no_judge_criterion_charges_a_justification():
    justified = sorted(
        label
        for label, case in measured_cases()
        if any(JUSTIFICATION_CLAUSE.search(rubric) for rubric in judge_criteria(case))
    )
    assert not justified, (
        f"these criteria grade an explanation instead of the observable act: {justified}"
    )


def test_substring_assertions_cannot_grade_vocabulary():
    loose = sorted(
        f"{label}: {text!r}"
        for label, case in measured_cases()
        for text in case.get("assercoes", {}).get("contem", [])
        if " " in text
    ) + sorted(
        f"{label}: {text!r}"
        for label, case in measured_cases()
        for text in case.get("assercoes", {}).get("nao_contem", [])
        if " " not in text
    )
    assert not loose, (
        "a required substring must be one exact token and a forbidden one must be "
        f"the specific wrong answer, not a loose word: {loose}"
    )
