from integration_models import AssertionResult, SessionTrace
from integration_session import extract_tool_name_sequence


def check_tool_ordering_assertion(
    trace: SessionTrace,
    assertion: dict,
) -> AssertionResult:
    tool_that_must_come_first = assertion["tool"]
    tool_that_must_come_after = assertion["before"]
    tool_sequence = extract_tool_name_sequence(trace)

    first_index = next(
        (
            index
            for index, name in enumerate(tool_sequence)
            if name == tool_that_must_come_first
        ),
        None,
    )
    second_index = next(
        (
            index
            for index, name in enumerate(tool_sequence)
            if name == tool_that_must_come_after
        ),
        None,
    )

    if first_index is None:
        return AssertionResult(
            name=(f"{tool_that_must_come_first} before {tool_that_must_come_after}"),
            passed=False,
            detail=f"{tool_that_must_come_first} never called",
        )
    if second_index is None:
        return AssertionResult(
            name=(f"{tool_that_must_come_first} before {tool_that_must_come_after}"),
            passed=False,
            detail=f"{tool_that_must_come_after} never called",
        )

    passed = first_index < second_index
    return AssertionResult(
        name=(f"{tool_that_must_come_first} before {tool_that_must_come_after}"),
        passed=passed,
        detail=(
            f"order correct ({first_index} < {second_index})"
            if passed
            else (f"order wrong ({first_index} >= {second_index})")
        ),
    )


def check_tool_presence_assertion(
    trace: SessionTrace,
    required_tool: str,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    present = required_tool in tool_sequence
    call_count = tool_sequence.count(required_tool)
    return AssertionResult(
        name=f"uses {required_tool}",
        passed=present,
        detail=(
            f"{required_tool} called {call_count} time(s)"
            if present
            else (f"{required_tool} never called. Tools used: {tool_sequence}")
        ),
    )


def check_tool_absence_assertion(
    trace: SessionTrace,
    forbidden_tool: str,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    absent = forbidden_tool not in tool_sequence
    call_count = tool_sequence.count(forbidden_tool)
    return AssertionResult(
        name=f"does not use {forbidden_tool}",
        passed=absent,
        detail=(
            f"{forbidden_tool} correctly absent"
            if absent
            else (f"{forbidden_tool} called {call_count} time(s)")
        ),
    )


def check_read_to_edit_ratio_assertion(
    trace: SessionTrace,
    minimum_ratio: float,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    read_count = tool_sequence.count("Read")
    edit_count = tool_sequence.count("Edit") + tool_sequence.count("Write")

    if edit_count == 0:
        return AssertionResult(
            name=f"read-to-edit ratio >= {minimum_ratio}",
            passed=False,
            detail="no edits made - agent did not act",
        )

    actual_ratio = read_count / edit_count
    passed = actual_ratio >= minimum_ratio
    return AssertionResult(
        name=f"read-to-edit ratio >= {minimum_ratio}",
        passed=passed,
        detail=(f"ratio {actual_ratio:.1f} ({read_count} reads / {edit_count} edits)"),
    )


def check_minimum_tool_count_assertion(
    trace: SessionTrace,
    tool_name: str,
    minimum_count: int,
) -> AssertionResult:
    tool_sequence = extract_tool_name_sequence(trace)
    actual_count = tool_sequence.count(tool_name)
    passed = actual_count >= minimum_count
    return AssertionResult(
        name=f"{tool_name} called >= {minimum_count} times",
        passed=passed,
        detail=f"called {actual_count} time(s)",
    )
