import json
import subprocess
import sys
import time

RUN_LIST_FIELDS = "workflowName,status,conclusion,url"
RUN_LIST_LIMIT = "50"
SECONDS_BETWEEN_POLLS = 15
POLLS_WAITING_FOR_RUNS_TO_APPEAR = 8
POLLS_WAITING_FOR_RUNS_TO_COMPLETE = 40
CONCLUSIONS_THAT_ARE_NOT_FAILURES = frozenset({"success", "skipped", "neutral"})

EXIT_CODE_CI_IS_RED = 1
EXIT_CODE_CI_VERDICT_UNKNOWN = 2


def resolve_commit_sha(commit_reference: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", commit_reference],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def fetch_runs_for_commit(commit_sha: str) -> list[dict]:
    completed = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--commit",
            commit_sha,
            "--limit",
            RUN_LIST_LIMIT,
            "--json",
            RUN_LIST_FIELDS,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def pending_runs(runs: list[dict]) -> list[dict]:
    return [run for run in runs if run["status"] != "completed"]


def failed_runs(runs: list[dict]) -> list[dict]:
    return [
        run
        for run in runs
        if run["conclusion"] not in CONCLUSIONS_THAT_ARE_NOT_FAILURES
    ]


def describe_run(run: dict) -> str:
    outcome = run["conclusion"] or run["status"]
    return f"{outcome:>12}  {run['workflowName']}  {run['url']}"


def wait_for_runs_to_appear(commit_sha: str) -> list[dict]:
    for poll in range(POLLS_WAITING_FOR_RUNS_TO_APPEAR):
        runs = fetch_runs_for_commit(commit_sha)
        if runs:
            return runs
        if poll + 1 < POLLS_WAITING_FOR_RUNS_TO_APPEAR:
            time.sleep(SECONDS_BETWEEN_POLLS)
    return []


def wait_for_runs_to_complete(commit_sha: str, runs: list[dict]) -> list[dict]:
    for _ in range(POLLS_WAITING_FOR_RUNS_TO_COMPLETE):
        if not pending_runs(runs):
            return runs
        time.sleep(SECONDS_BETWEEN_POLLS)
        runs = fetch_runs_for_commit(commit_sha)
    return runs


def report_runs(runs: list[dict]) -> None:
    for run in runs:
        print(describe_run(run))


def main() -> int:
    commit_reference = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    commit_sha = resolve_commit_sha(commit_reference)
    print(f"waiting on GitHub Actions for {commit_sha}")

    appeared_runs = wait_for_runs_to_appear(commit_sha)
    if not appeared_runs:
        print(
            f"no GitHub Actions run is registered for {commit_sha}: the commit was "
            f"never pushed, or no workflow matches it",
            file=sys.stderr,
        )
        return EXIT_CODE_CI_VERDICT_UNKNOWN

    runs = wait_for_runs_to_complete(commit_sha, appeared_runs)
    report_runs(runs)

    incomplete_runs = pending_runs(runs)
    if incomplete_runs:
        print(
            f"{len(incomplete_runs)} of {len(runs)} runs are still going after the "
            f"wait budget, so CI has no verdict yet",
            file=sys.stderr,
        )
        return EXIT_CODE_CI_VERDICT_UNKNOWN

    failures = failed_runs(runs)
    if failures:
        print(
            f"CI is red for {commit_sha}: {len(failures)} of {len(runs)} runs failed",
            file=sys.stderr,
        )
        return EXIT_CODE_CI_IS_RED

    print(f"CI is green for {commit_sha}: {len(runs)} runs succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
