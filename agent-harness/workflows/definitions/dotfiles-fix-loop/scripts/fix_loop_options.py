import dataclasses

DONE = "done"
RETRY = "retry"
RETRY_DEEPER = "retry-deeper"
ESCALATE = "escalate"
MERGE = "merge"
BLOCKING_SEVERITIES = frozenset({"critical", "high"})


@dataclasses.dataclass(frozen=True)
class LoopState:
    passed: bool
    iteration: int
    max_iterations: int
    failure_signature: str
    previous_signature: str


@dataclasses.dataclass(frozen=True)
class Legal:
    options: tuple[str, ...]
    reason: str
    guarded: bool


def next_step_options(state: LoopState) -> Legal:
    if state.passed:
        return Legal((DONE,), "the scoped test and every gate pass", False)
    if state.iteration >= state.max_iterations:
        return Legal(
            (ESCALATE,),
            f"the fix loop reached its cap of {state.max_iterations} iterations",
            True,
        )
    if state.failure_signature == state.previous_signature:
        return Legal((ESCALATE,), "the same failure repeated after an edit", True)
    return Legal(
        (RETRY, RETRY_DEEPER, ESCALATE),
        f"iteration {state.iteration} of {state.max_iterations} still fails",
        False,
    )


def blocking_findings(findings: list[dict]) -> list[dict]:
    return [
        finding
        for finding in findings
        if finding.get("severity") in BLOCKING_SEVERITIES
    ]


def merge_options(loop_choice: str, findings: list[dict]) -> Legal:
    if loop_choice != DONE:
        return Legal((ESCALATE,), "the fix loop stopped without a green test", True)
    blockers = len(blocking_findings(findings))
    if blockers:
        return Legal(
            (ESCALATE,), f"the review raised {blockers} blocking findings", True
        )
    if not findings:
        return Legal((MERGE,), "the test is green and the review found nothing", False)
    return Legal(
        (MERGE, ESCALATE),
        f"the test is green and the review raised {len(findings)} minor findings",
        False,
    )
