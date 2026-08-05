from pathlib import Path

import yaml

CALIBRATION_PATH = (
    Path(__file__).resolve().parent / "calibration" / "judge_calibration.yaml"
)


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


def judge_agreement(labeled_cases: list[dict], judge) -> dict:
    agreements = 0
    judge_pass = 0
    human_pass = 0
    disagreements = []
    for case in labeled_cases:
        human_passed = case["human_label"].strip().upper() == "PASS"
        judged_passed, reason = judge(case["rubric"], case["output"])
        if judged_passed == human_passed:
            agreements += 1
        else:
            disagreements.append(
                {
                    "name": case.get("name", "unnamed"),
                    "human": human_passed,
                    "judge": judged_passed,
                    "reason": reason,
                }
            )
        if judged_passed:
            judge_pass += 1
        if human_passed:
            human_pass += 1

    n = len(labeled_cases)
    return {
        "n": n,
        "agreements": agreements,
        "accuracy": agreements / n if n else 0.0,
        "cohens_kappa": cohens_kappa(n, agreements, judge_pass, human_pass),
        "disagreements": disagreements,
    }
