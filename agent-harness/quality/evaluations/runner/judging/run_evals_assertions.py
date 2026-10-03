import re


def check_assertions(output: str, assertions: dict, judge=None) -> list[str]:
    failures = _check_output_contains(output, assertions)
    failures.extend(_check_output_not_contains(output, assertions))
    failures.extend(_check_output_contains_any(output, assertions))
    failures.extend(_check_output_equals(output, assertions))
    failures.extend(_check_output_matches_regex(output, assertions))
    failures.extend(_check_output_not_matches_regex(output, assertions))
    failures.extend(_check_ordered_assertion(output, assertions))
    failures.extend(_check_llm_assertion(output, assertions, judge))
    return failures


def _check_output_contains(output: str, assertions: dict) -> list[str]:
    failures = []
    for expected in assertions.get("output_contains", []):
        if expected.lower() not in output.lower():
            failures.append(f"Expected '{expected}' in output")
    return failures


def _check_output_not_contains(output: str, assertions: dict) -> list[str]:
    failures = []
    for forbidden in assertions.get("output_not_contains", []):
        if forbidden.lower() in output.lower():
            failures.append(f"Unexpected '{forbidden}' in output")
    return failures


def _check_output_contains_any(output: str, assertions: dict) -> list[str]:
    if "output_contains_any" not in assertions:
        return []
    expected_values = assertions["output_contains_any"]
    found = any(exp.lower() in output.lower() for exp in expected_values)
    if found:
        return []
    return [f"Expected one of {expected_values} in output"]


def _check_output_equals(output: str, assertions: dict) -> list[str]:
    if "output_equals" not in assertions:
        return []
    accepted_values = assertions["output_equals"]
    normalized_output = output.strip().lower()
    normalized_values = [expected.strip().lower() for expected in accepted_values]
    if normalized_output in normalized_values:
        return []
    return [
        f"Expected output to equal one of {accepted_values}, got '{output.strip()}'"
    ]


def _check_output_matches_regex(output: str, assertions: dict) -> list[str]:
    failures = []
    for pattern in assertions.get("output_matches_regex", []):
        if re.search(pattern, output, re.IGNORECASE | re.MULTILINE) is None:
            failures.append(f"Expected output to match /{pattern}/")
    return failures


def _check_output_not_matches_regex(output: str, assertions: dict) -> list[str]:
    failures = []
    for pattern in assertions.get("output_not_matches_regex", []):
        if re.search(pattern, output, re.IGNORECASE | re.MULTILINE) is not None:
            failures.append(f"Output must not match /{pattern}/")
    return failures


def _check_ordered_assertion(output: str, assertions: dict) -> list[str]:
    if "output_contains_ordered" not in assertions:
        return []
    ordered_values = assertions["output_contains_ordered"]
    return _check_ordered_substrings(output, ordered_values)


def _check_llm_assertion(output: str, assertions: dict, judge) -> list[str]:
    if "llm_judge" not in assertions:
        return []
    judge_criteria = assertions["llm_judge"]
    return _check_llm_judge_rubrics(output, judge_criteria, judge)


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
