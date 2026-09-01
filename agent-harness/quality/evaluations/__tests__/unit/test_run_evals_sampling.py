from collections import namedtuple

import run_evals_sampling
from run_evals_sampling import (
    aggregate_repeated_runs,
    build_epoch_enriched_baseline,
    suite_pass_at_k,
)

FakeResult = namedtuple("FakeResult", ["name", "passed", "category"])

EXECUTION_PROFILE = {
    "subject": {"harness": "claude", "model": "sonnet", "reasoning_effort": "high"},
    "judge": {"harness": "claude", "model": "opus", "reasoning_effort": None},
}
TOKEN_USAGE = {"input_tokens": 100, "output_tokens": 50}


def _isolate_baseline(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals_sampling, "BASELINE_PATH", tmp_path / "baseline.json")


def _epoch(*items):
    results = []
    for item in items:
        name, passed = item[0], item[1]
        category = item[2] if len(item) > 2 else "core_rules"
        results.append(FakeResult(name, passed, category))
    return results


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


def test_aggregate_carries_the_authored_category():
    per_test = aggregate_repeated_runs([_epoch(("a", True, "delegation"))])
    assert per_test[0]["category"] == "delegation"


def test_aggregate_keeps_same_name_in_different_categories_separate():
    per_test = aggregate_repeated_runs(
        [
            _epoch(("shared", True, "nix/rebuild"), ("shared", False, "nix/knowledge")),
            _epoch(("shared", True, "nix/rebuild"), ("shared", False, "nix/knowledge")),
        ]
    )

    by_key = {(test["category"], test["name"]): test for test in per_test}
    assert len(per_test) == 2
    assert by_key[("nix/rebuild", "shared")]["passes"] == 2
    assert by_key[("nix/rebuild", "shared")]["total"] == 2
    assert by_key[("nix/knowledge", "shared")]["passes"] == 0
    assert by_key[("nix/knowledge", "shared")]["total"] == 2


def test_epoch_baseline_ties_toward_pass_on_an_even_split(tmp_path, monkeypatch):
    _isolate_baseline(tmp_path, monkeypatch)
    per_test = aggregate_repeated_runs(
        [
            _epoch(("even", True, "core_rules")),
            _epoch(("even", False, "core_rules")),
        ]
    )

    baseline = build_epoch_enriched_baseline(
        per_test,
        2,
        "abc123",
        "2026-07-23T00:00:00+00:00",
        EXECUTION_PROFILE,
        TOKEN_USAGE,
    )

    assert baseline["categories"]["core_rules"]["passed"] == 1
    assert baseline["categories"]["core_rules"]["failed"] == 0


def test_epoch_baseline_buckets_by_category_and_uses_majority_vote(
    tmp_path, monkeypatch
):
    _isolate_baseline(tmp_path, monkeypatch)
    per_test = aggregate_repeated_runs(
        [
            _epoch(
                ("solid", True, "workflow_compliance"), ("flaky", True, "core_rules")
            ),
            _epoch(
                ("solid", True, "workflow_compliance"), ("flaky", False, "core_rules")
            ),
            _epoch(
                ("solid", True, "workflow_compliance"), ("flaky", False, "core_rules")
            ),
        ]
    )

    baseline = build_epoch_enriched_baseline(
        per_test,
        3,
        "abc123",
        "2026-07-23T00:00:00+00:00",
        EXECUTION_PROFILE,
        TOKEN_USAGE,
    )

    assert baseline["total_tests"] == 2
    assert baseline["categories"]["workflow_compliance"]["passed"] == 1
    assert baseline["categories"]["core_rules"]["failed"] == 1
    assert baseline["total_passed"] == 1
    assert baseline["pass_rate"] == 0.5
    assert baseline["sampling"]["epochs"] == 3
    assert baseline["sampling"]["total_samples"] == 6
    assert baseline["sampling"]["flaky_tests"] == ["flaky"]
    assert baseline["execution_profile"] == EXECUTION_PROFILE
    assert baseline["token_usage"] == TOKEN_USAGE


def test_epoch_baseline_carries_provenance_and_omits_pass_at_2_for_one_epoch(
    tmp_path, monkeypatch
):
    _isolate_baseline(tmp_path, monkeypatch)
    per_test = aggregate_repeated_runs([_epoch(("a", True, "review"))])

    baseline = build_epoch_enriched_baseline(
        per_test,
        1,
        "deadbeef",
        "2026-07-23T00:00:00+00:00",
        EXECUTION_PROFILE,
        TOKEN_USAGE,
    )

    assert baseline["git_commit"] == "deadbeef"
    assert baseline["generated_at"] == "2026-07-23T00:00:00+00:00"
    assert baseline["sampling"]["suite_pass_at_2"] is None
    assert baseline["sampling"]["suite_pass_at_1"] == 1.0


def test_full_epoch_baseline_replaces_another_execution_profile(tmp_path, monkeypatch):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text('{"execution_profile":{"subject":{"harness":"codex"}}}')
    monkeypatch.setattr(run_evals_sampling, "BASELINE_PATH", baseline_path)
    per_test = aggregate_repeated_runs([_epoch(("a", True, "review"))])

    baseline = build_epoch_enriched_baseline(
        per_test,
        3,
        "deadbeef",
        "2026-07-23T00:00:00+00:00",
        EXECUTION_PROFILE,
        TOKEN_USAGE,
    )

    assert baseline["execution_profile"] == EXECUTION_PROFILE
