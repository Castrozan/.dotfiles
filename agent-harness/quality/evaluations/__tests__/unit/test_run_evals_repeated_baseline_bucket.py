from run_evals_baseline_record import (
    get_current_git_commit,
    repeated_outcomes_category_bucket,
)
from run_evals_execution_profile import execution_profile_identifier


EXECUTION_PROFILE = {"subject": {"harness": "codex"}, "judge": {"harness": "codex"}}


def test_repeated_outcomes_become_a_majority_graded_category_bucket():
    bucket = repeated_outcomes_category_bucket(
        {
            "category::stable": [True, True, True],
            "category::flaky": [True, False, True],
            "category::failed": [False, False, False],
        },
        {
            "category::stable": "stable-sha",
            "category::flaky": "flaky-sha",
            "category::failed": "failed-sha",
        },
        "2026-09-01T00:00:00+00:00",
        EXECUTION_PROFILE,
    )

    assert bucket["passed"] == 2
    assert bucket["failed"] == 1
    assert bucket["tests"][1] == {
        "name": "flaky",
        "passed": True,
        "passes": 2,
        "samples": 3,
        "fingerprint": "flaky-sha",
        "generated_at": "2026-09-01T00:00:00+00:00",
        "execution_profile_id": execution_profile_identifier(EXECUTION_PROFILE),
        "run_source": {
            "kind": "repeated_sampling",
            "git_commit": get_current_git_commit(),
        },
    }
