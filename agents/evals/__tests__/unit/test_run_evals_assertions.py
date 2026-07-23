from run_evals_assertions import check_assertions


def test_output_contains_passes_and_reports_missing_substring():
    assert check_assertions("hello world", {"output_contains": ["hello"]}) == []
    failures = check_assertions("hello world", {"output_contains": ["missing"]})
    assert failures == ["Expected 'missing' in output"]


def test_output_not_contains_flags_forbidden_substring():
    assert check_assertions("clean output", {"output_not_contains": ["error"]}) == []
    failures = check_assertions("an error occurred", {"output_not_contains": ["error"]})
    assert failures == ["Unexpected 'error' in output"]


def test_output_contains_any_requires_at_least_one_match():
    assert check_assertions("yes indeed", {"output_contains_any": ["no", "yes"]}) == []
    failures = check_assertions("maybe", {"output_contains_any": ["no", "yes"]})
    assert len(failures) == 1


def test_output_matches_regex_searches_case_insensitively():
    passing = {"output_matches_regex": [r"exit code \d"]}
    assert check_assertions("EXIT CODE 0 returned", passing) == []
    failures = check_assertions("no numeric code here", passing)
    assert len(failures) == 1


def test_output_not_matches_regex_flags_a_forbidden_pattern():
    forbidden = {"output_not_matches_regex": [r"FAIL\w*"]}
    assert check_assertions("all good", forbidden) == []
    failures = check_assertions("the run FAILED", forbidden)
    assert len(failures) == 1


def test_output_contains_ordered_requires_the_sequence_in_order():
    ordered = {"output_contains_ordered": ["first", "second", "third"]}
    assert check_assertions("first, then second, then third", ordered) == []
    assert len(check_assertions("third second first", ordered)) == 1


def test_output_contains_ordered_reports_the_first_missing_item():
    ordered = {"output_contains_ordered": ["alpha", "omega"]}
    failures = check_assertions("alpha only", ordered)
    assert failures == ["Expected 'omega' to appear after the preceding ordered items"]


def test_llm_judge_passes_when_the_injected_judge_approves():
    assert (
        check_assertions(
            "response",
            {"llm_judge": ["some rubric"]},
            judge=lambda rubric, output: (True, "meets rubric"),
        )
        == []
    )


def test_llm_judge_reports_the_reason_when_the_judge_rejects():
    failures = check_assertions(
        "response",
        {"llm_judge": [{"rubric": "be correct"}]},
        judge=lambda rubric, output: (False, "misses the point"),
    )
    assert failures == ["llm_judge rubric failed: be correct (misses the point)"]


def test_llm_judge_fails_loudly_when_no_judge_is_configured():
    failures = check_assertions(
        "response", {"llm_judge": ["needs a judge"]}, judge=None
    )
    assert failures == [
        "llm_judge rubric requested but no judge configured: needs a judge"
    ]


def test_llm_judge_hands_the_rubric_and_output_to_the_judge():
    captured = {}

    def recording_judge(rubric, output):
        captured["rubric"] = rubric
        captured["output"] = output
        return True, "ok"

    check_assertions(
        "the output text",
        {"llm_judge": ["the rubric text"]},
        judge=recording_judge,
    )
    assert captured == {"rubric": "the rubric text", "output": "the output text"}
