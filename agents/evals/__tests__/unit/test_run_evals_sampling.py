from collections import namedtuple

from run_evals_sampling import aggregate_repeated_runs, suite_pass_at_k

FakeResult = namedtuple("FakeResult", ["name", "passed"])


def _epoch(*pairs):
    return [FakeResult(name, passed) for name, passed in pairs]


def test_aggregate_counts_passes_and_flags_flaky_tests():
    per_test = aggregate_repeated_runs(
        [
            _epoch(("a", True), ("b", True)),
            _epoch(("a", True), ("b", False)),
            _epoch(("a", True), ("b", True)),
        ]
    )
    by_name = {test["name"]: test for test in per_test}
    assert by_name["a"]["passes"] == 3 and by_name["a"]["total"] == 3
    assert by_name["a"]["flaky"] is False
    assert by_name["b"]["passes"] == 2 and by_name["b"]["total"] == 3
    assert by_name["b"]["flaky"] is True
    assert by_name["b"]["lower"] < by_name["b"]["upper"]


def test_suite_pass_at_k_is_one_when_every_test_always_passes():
    per_test = aggregate_repeated_runs([_epoch(("a", True)), _epoch(("a", True))])
    assert suite_pass_at_k(per_test, 1) == 1.0


def test_suite_pass_at_k_rewards_retries_on_a_flaky_test():
    per_test = aggregate_repeated_runs(
        [
            _epoch(("a", True)),
            _epoch(("a", False)),
            _epoch(("a", True)),
            _epoch(("a", False)),
        ]
    )
    assert suite_pass_at_k(per_test, 2) > suite_pass_at_k(per_test, 1)


def test_suite_pass_at_k_handles_no_tests():
    assert suite_pass_at_k([], 1) == 0.0
