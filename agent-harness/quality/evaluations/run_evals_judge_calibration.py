from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import yaml

CALIBRATION_PATH = (
    Path(__file__).resolve().parent / "calibration" / "judge_calibration.yaml"
)
MINIMUM_BALANCED_ACCURACY = 0.8
MINIMUM_FAILED_CASE_RECALL = 0.8
MINIMUM_COHENS_KAPPA = 0.7


def load_calibration_cases(path: Path = CALIBRATION_PATH) -> list[dict]:
    data = yaml.safe_load(path.read_text())
    return data.get("cases", [])


def cohens_kappa(n: int, agreements: int, judge_pass: int, human_pass: int) -> float:
    if n == 0:
        return 0.0
    observed = agreements / n
    p_judge_pass = judge_pass / n
    p_human_pass = human_pass / n
    expected = p_judge_pass * p_human_pass + (1 - p_judge_pass) * (1 - p_human_pass)
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def agreement_metrics(predictions: list[dict]) -> dict:
    true_positive = sum(item["human"] and item["judge"] for item in predictions)
    true_negative = sum(not item["human"] and not item["judge"] for item in predictions)
    false_positive = sum(not item["human"] and item["judge"] for item in predictions)
    false_negative = sum(item["human"] and not item["judge"] for item in predictions)
    pass_total = true_positive + false_negative
    fail_total = true_negative + false_positive
    pass_recall = true_positive / pass_total if pass_total else 1.0
    failed_case_recall = true_negative / fail_total if fail_total else 1.0
    n = len(predictions)
    agreements = true_positive + true_negative
    kappa = cohens_kappa(
        n,
        agreements,
        true_positive + false_positive,
        true_positive + false_negative,
    )
    balanced_accuracy = (pass_recall + failed_case_recall) / 2
    return {
        "n": n,
        "agreements": agreements,
        "accuracy": agreements / n if n else 0.0,
        "cohens_kappa": kappa,
        "balanced_accuracy": balanced_accuracy,
        "failed_case_recall": failed_case_recall,
        "confusion_matrix": {
            "tp": true_positive,
            "tn": true_negative,
            "fp": false_positive,
            "fn": false_negative,
        },
        "meets_gate": (
            balanced_accuracy >= MINIMUM_BALANCED_ACCURACY
            and failed_case_recall >= MINIMUM_FAILED_CASE_RECALL
            and kappa >= MINIMUM_COHENS_KAPPA
        ),
    }


def judge_agreement(labeled_cases: list[dict], judge, max_workers: int = 4) -> dict:
    predictions = []
    disagreements = []

    def grade(case):
        judged_passed, reason = judge(case["rubric"], case["output"])
        return case, judged_passed, reason

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        graded_cases = list(executor.map(grade, labeled_cases))

    for case, judged_passed, reason in graded_cases:
        human_passed = case["human_label"].strip().upper() == "PASS"
        prediction = {
            "human": human_passed,
            "judge": judged_passed,
            "family": case.get("rubric_family", "unspecified"),
        }
        predictions.append(prediction)
        if judged_passed != human_passed:
            disagreements.append(
                {
                    "name": case.get("name", "unnamed"),
                    "human": human_passed,
                    "judge": judged_passed,
                    "reason": reason,
                }
            )

    result = agreement_metrics(predictions)
    result["by_family"] = {
        family: agreement_metrics(
            [item for item in predictions if item["family"] == family]
        )
        for family in sorted({item["family"] for item in predictions})
    }
    result["disagreements"] = disagreements
    return result
