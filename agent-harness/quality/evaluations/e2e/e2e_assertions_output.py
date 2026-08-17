from e2e_models import E2eAssertionResult, TerminalSessionTrace


def final_assistant_output(trace: TerminalSessionTrace) -> str:
    if not trace.detected_assistant_text_blocks:
        return ""
    return trace.detected_assistant_text_blocks[-1]


def check_output_contains_assertion(
    trace: TerminalSessionTrace, expected: str
) -> E2eAssertionResult:
    found = expected.lower() in final_assistant_output(trace).lower()
    return E2eAssertionResult(
        name=f"final output contains '{expected}'",
        passed=found,
        detail="found" if found else "not found",
    )


def check_output_not_contains_assertion(
    trace: TerminalSessionTrace, forbidden: str
) -> E2eAssertionResult:
    absent = forbidden.lower() not in final_assistant_output(trace).lower()
    return E2eAssertionResult(
        name=f"final output excludes '{forbidden}'",
        passed=absent,
        detail="absent" if absent else "found",
    )


def check_output_maximum_words_assertion(
    trace: TerminalSessionTrace, maximum_words: int
) -> E2eAssertionResult:
    word_count = len(final_assistant_output(trace).split())
    return E2eAssertionResult(
        name=f"final output uses at most {maximum_words} words",
        passed=word_count <= maximum_words,
        detail=f"found {word_count} words",
    )
