import argparse
import json
import sys
from pathlib import Path

from fix_loop_checkout import tail
from fix_loop_options import (
    DONE,
    ESCALATE,
    MERGE,
    RETRY,
    RETRY_DEEPER,
    Legal,
    LoopState,
    merge_options,
    next_step_options,
)

CONFIDENCE_FLOOR = 0.6
EVIDENCE_TAIL_LINES = 60
CONTEXT = (
    "You steer an automated code-fix workflow in a git repository. A small coding "
    "model edits files; code runs the formatters, the lint gate and the scoped test "
    "after every edit. Choose one of the offered options only."
)
DESCRIPTIONS = {
    DONE: "The scoped test and every gate pass, so the change goes to review.",
    RETRY: (
        "Run the small fixer again at low effort on the new failure: the last edit "
        "moved the failure and a quick follow-up edit should finish the fix."
    ),
    RETRY_DEEPER: (
        "Run the small fixer at medium effort: the failure needs more reasoning than "
        "a quick edit, such as a wrong approach or a cause the last edit missed."
    ),
    ESCALATE: (
        "Stop and hand the change to a person: the failure lies outside the task, is "
        "environmental, needs a decision the task does not settle, or edits go in "
        "circles."
    ),
    MERGE: (
        "Recommend merging: the remaining review findings are minor and need no "
        "change before the fix is pushed."
    ),
}
MERGE_DESCRIPTIONS = DESCRIPTIONS | {
    ESCALATE: (
        "Recommend holding the change for a person: a finding should be fixed or "
        "judged before the change is pushed."
    )
}
NEXT_INSTRUCTIONS = (
    "Which next step gives the best chance of a correct, in-scope fix without "
    "wasting attempts?"
)
MERGE_INSTRUCTIONS = (
    "Given the task, the green scoped test and the review findings, should the "
    "change be pushed as it is, or wait for a person?"
)


def artifact_tail(artifacts: Path, name: str) -> str:
    path = artifacts / name
    return tail(path.read_text(), EVIDENCE_TAIL_LINES) if path.is_file() else ""


def request(
    decision: str, legal: Legal, evidence: str, summary: str, descriptions: dict
) -> dict:
    return {
        "decision": decision,
        "instructions": NEXT_INSTRUCTIONS if decision == "next" else MERGE_INSTRUCTIONS,
        "context": CONTEXT,
        "evidence": evidence,
        "options": [
            {"id": option, "description": descriptions[option]}
            for option in legal.options
        ],
        "safest": ESCALATE,
        "floor": CONFIDENCE_FLOOR,
        "reason": legal.reason,
        "guarded": legal.guarded,
        "summary": summary,
    }


def prior_next_decisions(artifacts: Path) -> int:
    record = artifacts / "decisions.jsonl"
    if not record.is_file():
        return 0
    entries = [json.loads(line) for line in record.read_text().splitlines() if line]
    return sum(1 for entry in entries if entry.get("decision") == "next")


def next_request(arguments: argparse.Namespace, checked: dict) -> dict:
    artifacts = arguments.artifacts
    state = LoopState(
        passed=bool(checked["passed"]),
        iteration=prior_next_decisions(artifacts) + 1,
        max_iterations=arguments.max_iterations,
        failure_signature=checked["failure_signature"],
        previous_signature=arguments.previous_signature,
    )
    legal = next_step_options(state)
    evidence = (
        f"Task:\n{(artifacts / 'task.txt').read_text()}\n\n"
        f"Iteration {state.iteration} of {state.max_iterations}. Scoped test "
        f"passed: {checked['tests_passed']}. Gates passed: {checked['gates_passed']}. "
        f"Failure changed since the last iteration: "
        f"{state.failure_signature != state.previous_signature}.\n\n"
        f"Changed files: {', '.join(checked['changed_files']) or 'none'}\n\n"
        f"Scoped test output tail:\n{artifact_tail(artifacts, 'test.log')}\n\n"
        f"Gate output tail:\n{artifact_tail(artifacts, 'gate.log')}"
    )
    summary = f"Iteration {state.iteration}: {legal.reason}."
    return request("next", legal, evidence, summary, DESCRIPTIONS)


def rendered_finding(finding: dict) -> str:
    return (
        f"- {finding.get('severity')} {finding.get('file')}:{finding.get('line')} "
        f"{finding.get('title')}: {finding.get('detail')}"
    )


def merge_request(arguments: argparse.Namespace, outcome: dict) -> dict:
    artifacts = arguments.artifacts
    findings = outcome["review"]["findings"]
    legal = merge_options(outcome["loop"]["choice"], findings)
    task = (artifacts / "task.txt").read_text()
    evidence = (
        f"Task:\n{task}\n\nThe fix loop ended with {outcome['loop']['choice']}. "
        "Review findings:\n" + ("\n".join(map(rendered_finding, findings)) or "none")
    )
    summary = (
        f"Push the fix for: {task.strip().splitlines()[0]}? {legal.reason}. "
        f"Diff: {artifacts / 'change.diff'}"
    )
    return request("merge", legal, evidence, summary, MERGE_DESCRIPTIONS)


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fix-loop-requests",
        description=(
            "Read a fix loop result on stdin, compute the legal options and print "
            "the decision request for workflow-decision."
        ),
    )
    parser.add_argument("decision", choices=["next", "merge"])
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--previous-signature", default="")
    parser.add_argument("--max-iterations", type=int, default=1)
    return parser.parse_args(command_line_arguments)


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    build = next_request if arguments.decision == "next" else merge_request
    print(json.dumps(build(arguments, json.load(sys.stdin))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
