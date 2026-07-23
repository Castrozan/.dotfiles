import re


def check_assertions(output: str, assertions: dict, judge=None) -> list[str]:
    failures = []

    if "output_contains" in assertions:
        for expected in assertions["output_contains"]:
            if expected.lower() not in output.lower():
                failures.append(f"Expected '{expected}' in output")

    if "output_not_contains" in assertions:
        for forbidden in assertions["output_not_contains"]:
            if forbidden.lower() in output.lower():
                failures.append(f"Unexpected '{forbidden}' in output")

    if "output_contains_any" in assertions:
        found = any(
            exp.lower() in output.lower() for exp in assertions["output_contains_any"]
        )
        if not found:
            failures.append(
                f"Expected one of {assertions['output_contains_any']} in output"
            )

    if "output_matches_regex" in assertions:
        for pattern in assertions["output_matches_regex"]:
            if re.search(pattern, output, re.IGNORECASE | re.MULTILINE) is None:
                failures.append(f"Expected output to match /{pattern}/")

    if "output_not_matches_regex" in assertions:
        for pattern in assertions["output_not_matches_regex"]:
            if re.search(pattern, output, re.IGNORECASE | re.MULTILINE) is not None:
                failures.append(f"Output must not match /{pattern}/")

    if "output_contains_ordered" in assertions:
        failures.extend(
            _check_ordered_substrings(output, assertions["output_contains_ordered"])
        )

    if "llm_judge" in assertions:
        failures.extend(
            _check_llm_judge_rubrics(output, assertions["llm_judge"], judge)
        )

    return failures


def _check_ordered_substrings(output: str, ordered_substrings: list) -> list[str]:
    lowered_output = output.lower()
    search_start_index = 0
    for substring in ordered_substrings:
        found_index = lowered_output.find(substring.lower(), search_start_index)
        if found_index == -1:
            return [
                f"Expected '{substring}' to appear after the preceding ordered items"
            ]
        search_start_index = found_index + len(substring)
    return []


def _check_llm_judge_rubrics(output: str, judge_criteria: list, judge) -> list[str]:
    failures = []
    for criterion in judge_criteria:
        rubric = criterion["rubric"] if isinstance(criterion, dict) else criterion
        if judge is None:
            failures.append(
                f"llm_judge rubric requested but no judge configured: {rubric}"
            )
            continue
        passed, reason = judge(rubric, output)
        if not passed:
            failures.append(f"llm_judge rubric failed: {rubric} ({reason})")
    return failures
