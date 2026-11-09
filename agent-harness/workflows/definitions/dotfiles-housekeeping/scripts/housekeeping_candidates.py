import json
import sys

VERIFIER_COUNT = 5
MAXIMUM_CANDIDATES = 40
MINIMUM_CONFIDENCE = 3
NEARBY_LINE_DISTANCE = 2
VERIFIER_FIELDS = ("index", "file", "line", "dimension", "title", "detail")


def is_near(left: dict, right: dict) -> bool:
    return (
        left["file"] == right["file"]
        and abs(left["line"] - right["line"]) <= NEARBY_LINE_DISTANCE
    )


def distinct_findings(findings: list[dict]) -> list[dict]:
    return [
        finding
        for position, finding in enumerate(findings)
        if next(
            index
            for index, candidate in enumerate(findings)
            if is_near(candidate, finding)
        )
        == position
    ]


def ranked_candidates(findings: list[dict]) -> list[dict]:
    confident = [
        finding for finding in findings if finding["confidence"] >= MINIMUM_CONFIDENCE
    ]
    ranked = sorted(confident, key=lambda finding: -finding["confidence"])
    return [
        {**finding, "index": index}
        for index, finding in enumerate(ranked[:MAXIMUM_CANDIDATES])
    ]


def verifier_view(candidate: dict) -> dict:
    return {field: candidate[field] for field in VERIFIER_FIELDS}


def verifier_batches(candidates: list[dict]) -> list[list[dict]]:
    batches = [
        [
            verifier_view(candidate)
            for candidate in candidates
            if candidate["index"] % VERIFIER_COUNT == batch_index
        ]
        for batch_index in range(VERIFIER_COUNT)
    ]
    return [batch for batch in batches if batch]


def select_candidates(slice_results: list) -> dict:
    read_slices = [
        result["findings"]
        for result in slice_results
        if isinstance(result, dict) and "findings" in result
    ]
    distinct = distinct_findings(
        [finding for findings in read_slices for finding in findings]
    )
    candidates = ranked_candidates(distinct)
    return {
        "slices_read": len(read_slices),
        "distinct_count": len(distinct),
        "candidates": candidates,
        "batches": verifier_batches(candidates),
    }


def main() -> int:
    print(json.dumps(select_candidates(json.load(sys.stdin))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
