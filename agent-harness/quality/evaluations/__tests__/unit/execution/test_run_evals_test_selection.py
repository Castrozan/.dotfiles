from runner.execution.run_evals_test_selection import selected_tests

CONFIG = {
    "tests": {
        "skill_routing": [
            {"name": "seen", "prompt": "p"},
            {"name": "unseen", "prompt": "p", "held_out": True},
        ],
    },
}


def _selected_names(**filters):
    return [test["name"] for test, _ in selected_tests(CONFIG, None, None, **filters)]


def test_partition_keeps_held_out_cases_away_from_the_train_run():
    assert _selected_names(partition="train") == ["seen"]
    assert _selected_names(partition="held-out") == ["unseen"]
    assert _selected_names() == ["seen", "unseen"]
