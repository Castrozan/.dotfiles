from hypothesis import given
from hypothesis import strategies as strategies

from housekeeping_candidates import (
    MAXIMUM_CANDIDATES,
    MINIMUM_CONFIDENCE,
    VERIFIER_COUNT,
    select_candidates,
)
from housekeeping_report import compose_report

findings = strategies.fixed_dictionaries(
    {
        "dimension": strategies.sampled_from(["markers", "defects"]),
        "file": strategies.sampled_from(["a.py", "b.nix", "c.md"]),
        "line": strategies.integers(min_value=1, max_value=60),
        "severity": strategies.sampled_from(["critical", "high", "medium", "low"]),
        "title": strategies.text(max_size=10),
        "detail": strategies.text(max_size=10),
        "confidence": strategies.integers(min_value=1, max_value=5),
    }
)
slice_results = strategies.lists(
    strategies.one_of(
        strategies.fixed_dictionaries({"findings": strategies.lists(findings)}),
        strategies.just({"archon_failed": True, "status": "failed"}),
    ),
    max_size=12,
)


@given(slice_results)
def test_candidates_are_confident_distinct_ranked_and_capped(results):
    selection = select_candidates(results)
    candidates = selection["candidates"]
    assert len(candidates) <= MAXIMUM_CANDIDATES
    assert [candidate["index"] for candidate in candidates] == list(
        range(len(candidates))
    )
    assert all(
        candidate["confidence"] >= MINIMUM_CONFIDENCE for candidate in candidates
    )
    confidences = [candidate["confidence"] for candidate in candidates]
    assert confidences == sorted(confidences, reverse=True)
    for position, candidate in enumerate(candidates):
        for earlier in candidates[:position]:
            assert not (
                earlier["file"] == candidate["file"]
                and abs(earlier["line"] - candidate["line"]) <= 2
            )
    assert selection["slices_read"] == sum("findings" in result for result in results)


@given(slice_results)
def test_every_candidate_reaches_exactly_one_verifier_without_its_ranking(results):
    selection = select_candidates(results)
    batches = selection["batches"]
    assert len(batches) <= VERIFIER_COUNT
    assert all(batches)
    batched_indexes = sorted(item["index"] for batch in batches for item in batch)
    assert batched_indexes == [
        candidate["index"] for candidate in selection["candidates"]
    ]
    assert all(
        "confidence" not in item and "severity" not in item
        for batch in batches
        for item in batch
    )


def test_a_slicer_error_is_the_whole_report():
    report = compose_report(
        "tree",
        {
            "slice": {"slices": [], "error": "tree holds no tracked text files"},
            "candidates": {},
            "verdicts": [],
        },
    )
    assert report == "Housekeeping did not run: tree holds no tracked text files."


def test_confirmed_findings_are_reported_most_severe_first():
    candidate = {
        "dimension": "defects",
        "file": "a.py",
        "line": 3,
        "title": "Inverted guard",
        "detail": "Returns early on success.",
        "confidence": 5,
    }
    selection = {
        "slices_read": 1,
        "candidates": [
            {**candidate, "index": 0, "severity": "low"},
            {**candidate, "index": 1, "severity": "critical", "line": 30},
            {**candidate, "index": 2, "severity": "high", "line": 60},
        ],
        "batches": [[{"index": 0}], [{"index": 1}], [{"index": 2}]],
    }
    verdicts = [
        {"verdicts": [{"index": 0, "confirmed": True, "reason": "real"}]},
        {"verdicts": [{"index": 1, "confirmed": True, "reason": "real"}]},
        {"archon_failed": True},
    ]
    report = compose_report(
        "tree",
        {"slice": {"slices": ["s0"]}, "candidates": selection, "verdicts": verdicts},
    )
    assert report.splitlines() == [
        "Housekeeping of tree: 1 of 1 slices read twice, 3 candidates, "
        "2 of 3 verifier batches returned, 2 confirmed.",
        "- **critical** a.py:30 (defects): Inverted guard. Returns early on success.",
        "- **low** a.py:3 (defects): Inverted guard. Returns early on success.",
    ]
