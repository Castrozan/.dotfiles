import argparse
import json
import sys

MAXIMUM_REPORTED_FINDINGS = 15
SEVERITY_ORDER = ("critical", "high", "medium", "low")


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose the housekeeping report from the workflow's results."
    )
    parser.add_argument("--subtree", required=True)
    return parser.parse_args(command_line_arguments)


def confirmed_indexes(verifier_results: list) -> set[int]:
    return {
        verdict["index"]
        for result in verifier_results
        if isinstance(result, dict)
        for verdict in result.get("verdicts", [])
        if verdict.get("confirmed")
    }


def report_line(finding: dict) -> str:
    return (
        f"- **{finding['severity']}** {finding['file']}:{finding['line']} "
        f"({finding['dimension']}): {finding['title']}. {finding['detail']}"
    )


def compose_report(subtree: str, results: dict) -> str:
    sliced = results["slice"]
    if not sliced.get("slices"):
        reason = sliced.get("error") or "the slicer returned no slices"
        return f"Housekeeping did not run: {reason}."
    selection = results["candidates"]
    candidates = selection["candidates"]
    verifier_results = results["verdicts"]
    returned_batches = sum(
        isinstance(result, dict) and "verdicts" in result for result in verifier_results
    )
    confirmed = sorted(
        (
            candidate
            for candidate in candidates
            if candidate["index"] in confirmed_indexes(verifier_results)
        ),
        key=lambda candidate: SEVERITY_ORDER.index(candidate["severity"]),
    )
    summary = (
        f"Housekeeping of {subtree}: {selection['slices_read']} of "
        f"{len(sliced['slices'])} slices read twice, {len(candidates)} candidates, "
        f"{returned_batches} of {len(selection['batches'])} verifier batches "
        f"returned, {len(confirmed)} confirmed."
    )
    shown = confirmed[:MAXIMUM_REPORTED_FINDINGS]
    hidden = len(confirmed) - len(shown)
    hidden_line = [f"{hidden} more confirmed findings not shown."] if hidden else []
    return "\n".join([summary, *map(report_line, shown), *hidden_line])


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    print(compose_report(arguments.subtree, json.load(sys.stdin)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
