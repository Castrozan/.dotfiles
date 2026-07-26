from __future__ import annotations

import json
import re
from pathlib import Path

from run_evals_baseline_thresholds import (
    MAXIMUM_BASELINE_AGE_DAYS,
    MAXIMUM_REGRESSION_DROP,
)

CENTRAL_EVAL_SUITE_GLOB = "agents/__tests__/evals/*.yaml"
SKILL_EVAL_SUITE_GLOB = "agents/skills/*/__tests__/evals/*.yaml"
ADVERSARIAL_SUITE_RELATIVE_PATH = "agents/__tests__/evals/adversarial.yaml"
JUDGE_CALIBRATION_RELATIVE_PATH = "agents/__tests__/calibration/judge_calibration.yaml"
STATIC_EVAL_BASELINE_RELATIVE_PATH = "agents/__tests__/baseline.json"
INSTRUCTION_LOADING_EXPERIMENT_RELATIVE_PATH = (
    "agents/__tests__/instruction-loading-experiment.json"
)

RUBRIC_JUDGE_ASSERTION_NAME = "llm_judge"
TEST_CASE_HEADING_PATTERN = re.compile(r"^\s*-\s+name:", re.MULTILINE)
RECORDED_KAPPA_PATTERN = re.compile(r"^\s*cohens_kappa:\s*([0-9.]+)\s*$", re.MULTILINE)
RECORDED_CASE_COUNT_PATTERN = re.compile(r"^\s*cases:\s*([0-9]+)\s*$", re.MULTILINE)
SUBSTANTIAL_AGREEMENT_KAPPA = 0.6
GOLD_STANDARD_PRACTICE_COUNT = 7
PERCENTAGE_POINTS_PER_RATE = 100
PERCENTAGE_POINT_DECIMAL_PLACES = 2


def describe_practice(practice, adopted, measurement, measurement_unit, evidence):
    return {
        "practice": practice,
        "adopted": adopted,
        "measurement": measurement,
        "measurementUnit": measurement_unit,
        "evidence": evidence,
    }


def read_text_or_empty(document_path: Path) -> str:
    return document_path.read_text() if document_path.is_file() else ""


def read_json_or_empty(document_path: Path) -> dict:
    return json.loads(document_path.read_text()) if document_path.is_file() else {}


def read_first_captured_number(pattern, text, parse):
    match = pattern.search(text)
    return parse(match.group(1)) if match else 0


def discover_eval_suite_paths(repository_root: Path) -> list[Path]:
    return sorted(repository_root.glob(CENTRAL_EVAL_SUITE_GLOB)) + sorted(
        repository_root.glob(SKILL_EVAL_SUITE_GLOB)
    )


def measure_rubric_graded_judging(repository_root: Path) -> dict:
    suite_paths = discover_eval_suite_paths(repository_root)
    judged_suite_count = sum(
        1
        for suite_path in suite_paths
        if RUBRIC_JUDGE_ASSERTION_NAME in suite_path.read_text()
    )
    return describe_practice(
        "rubric-graded-judging",
        judged_suite_count > 0,
        judged_suite_count,
        f"of {len(suite_paths)} eval suites",
        "Responses are graded against a written rubric by a pinned judge model "
        "rather than scored on substring recall, so a right answer phrased "
        "unexpectedly still passes and a wrong answer carrying the magic word "
        "still fails.",
    )


def measure_judge_calibration(repository_root: Path) -> dict:
    calibration_text = read_text_or_empty(
        repository_root / JUDGE_CALIBRATION_RELATIVE_PATH
    )
    recorded_kappa = read_first_captured_number(
        RECORDED_KAPPA_PATTERN, calibration_text, float
    )
    labelled_case_count = read_first_captured_number(
        RECORDED_CASE_COUNT_PATTERN, calibration_text, int
    )
    return describe_practice(
        "judge-calibration",
        recorded_kappa >= SUBSTANTIAL_AGREEMENT_KAPPA,
        recorded_kappa,
        f"Cohen's kappa over {labelled_case_count} labelled cases",
        "The rubric judge is scored against a maintainer-labelled corpus, so its "
        "agreement with a human is a measured number instead of an assumption.",
    )


def measure_adversarial_testing(repository_root: Path) -> dict:
    injection_case_count = len(
        TEST_CASE_HEADING_PATTERN.findall(
            read_text_or_empty(repository_root / ADVERSARIAL_SUITE_RELATIVE_PATH)
        )
    )
    return describe_practice(
        "adversarial-testing",
        injection_case_count > 0,
        injection_case_count,
        "prompt-injection cases",
        "A dedicated suite drives injection attempts at the instruction surface "
        "and asserts the guard hooks refuse them.",
    )


def measure_repeated_sampling(repository_root: Path) -> dict:
    baseline = read_json_or_empty(repository_root / STATIC_EVAL_BASELINE_RELATIVE_PATH)
    epochs = baseline.get("sampling", {}).get("epochs", 1) if baseline else 0
    return describe_practice(
        "repeated-sampling",
        epochs > 1,
        epochs,
        "sampling epochs behind the committed baseline",
        "Rerunning every test across epochs turns one pass rate into a mean with "
        "an interval, so a flaky result reads as noise instead of a regression.",
    )


def measure_paired_significance(repository_root: Path) -> dict:
    experiment = read_json_or_empty(
        repository_root / INSTRUCTION_LOADING_EXPERIMENT_RELATIVE_PATH
    )
    paired_test_count = sum(
        category["paired_tests"]
        for category in experiment.get("categories", {}).values()
    )
    return describe_practice(
        "paired-significance",
        paired_test_count > 0,
        paired_test_count,
        "paired tests behind an exact McNemar test",
        "The instruction surface is measured against a stripped control arm on "
        "the same tests, so its reported effect is a paired delta carrying a "
        "p-value rather than a claim.",
    )


def measure_regression_gating() -> dict:
    percentage_points = round(
        MAXIMUM_REGRESSION_DROP * PERCENTAGE_POINTS_PER_RATE,
        PERCENTAGE_POINT_DECIMAL_PLACES,
    )
    return describe_practice(
        "regression-gating",
        0 < MAXIMUM_REGRESSION_DROP < 1,
        percentage_points,
        "percentage points of pass-rate drop before CI fails",
        "CI fails on a drop against the previous committed baseline and not only "
        "against an absolute floor, so drift is caught while the floor is still "
        "met.",
    )


def measure_baseline_freshness_gating() -> dict:
    return describe_practice(
        "baseline-freshness-gating",
        MAXIMUM_BASELINE_AGE_DAYS > 0,
        MAXIMUM_BASELINE_AGE_DAYS,
        "days before the committed baseline is refused as stale",
        "A baseline older than the window fails CI, so a green check cannot rest "
        "on a recording that predates the instructions it claims to cover.",
    )


def measure_gold_standard_practices(repository_root: Path) -> list[dict]:
    return [
        measure_rubric_graded_judging(repository_root),
        measure_judge_calibration(repository_root),
        measure_adversarial_testing(repository_root),
        measure_repeated_sampling(repository_root),
        measure_paired_significance(repository_root),
        measure_regression_gating(),
        measure_baseline_freshness_gating(),
    ]
