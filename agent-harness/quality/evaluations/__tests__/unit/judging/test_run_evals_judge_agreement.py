from runner.judging.run_evals_judge_calibration import judge_agreement, verdict_flips


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


def test_judge_agreement_reports_confusion_metrics_and_rubric_families():
    cases = [
        {
            "name": "reader-pass",
            "rubric_family": "reader_recovery",
            "rubric": "r",
            "output": "pass",
            "human_label": "PASS",
        },
        {
            "name": "reader-fail",
            "rubric_family": "reader_recovery",
            "rubric": "r",
            "output": "fail",
            "human_label": "FAIL",
        },
        {
            "name": "policy-fail",
            "rubric_family": "instruction_compliance",
            "rubric": "r",
            "output": "missed",
            "human_label": "FAIL",
        },
    ]

    result = judge_agreement(cases, lambda rubric, output: (output == "pass", "graded"))

    assert result["confusion_matrix"] == {"tp": 1, "tn": 2, "fp": 0, "fn": 0}
    assert result["balanced_accuracy"] == 1.0
    assert result["failed_case_recall"] == 1.0
    assert result["meets_gate"] is True
    assert set(result["by_family"]) == {
        "reader_recovery",
        "instruction_compliance",
    }


def test_grading_the_same_outputs_twice_names_every_flipped_verdict():
    cases = [
        {"name": "steady", "rubric": "r", "output": "steady", "human_label": "PASS"},
        {"name": "wobbly", "rubric": "r", "output": "wobbly", "human_label": "PASS"},
    ]
    first_pass = {"steady": True, "wobbly": True}
    second_pass = {"steady": True, "wobbly": False}

    passes = [
        judge_agreement(
            cases,
            lambda rubric, output, verdicts=verdicts: (verdicts[output], "reason"),
        )
        for verdicts in (first_pass, second_pass)
    ]

    assert passes[0]["verdicts"] == first_pass
    assert verdict_flips(passes) == ["wobbly"]
    assert verdict_flips(passes[:1]) == []
