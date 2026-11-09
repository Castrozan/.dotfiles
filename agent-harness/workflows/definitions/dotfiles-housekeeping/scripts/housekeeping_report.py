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


def confirmed_findings(candidates: list[dict], verifier_results: list) -> list[dict]:
    indexes = confirmed_indexes(verifier_results)
    return sorted(
        (candidate for candidate in candidates if candidate["index"] in indexes),
        key=lambda candidate: SEVERITY_ORDER.index(candidate["severity"]),
    )


def returned_batch_count(verifier_results: list) -> int:
    return sum(
        isinstance(result, dict) and "verdicts" in result for result in verifier_results
    )


def compose_report(subtree: str, results: dict) -> str:
    sliced = results["slice"]
    if not sliced.get("slices"):
        reason = sliced.get("error") or "the slicer returned no slices"
        return f"Housekeeping did not run: {reason}."
    selection = results["candidates"]
    confirmed = confirmed_findings(selection["candidates"], results["verdicts"])
    summary = (
        f"Housekeeping of {subtree}: {selection['slices_read']} of "
        f"{len(sliced['slices'])} slices read twice, "
        f"{len(selection['candidates'])} candidates, "
        f"{returned_batch_count(results['verdicts'])} of {len(selection['batches'])} "
        f"verifier batches returned, {len(confirmed)} confirmed."
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
