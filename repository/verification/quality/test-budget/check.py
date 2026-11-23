import json
import re
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
BUDGET_PATH = Path(__file__).resolve().parent / "budget.json"
GIT_TIMEOUT_SECONDS = 10
POLICY = "repository/verification/TESTING.md#what-earns-a-test"
SUITES = {
    "pytest": (
        re.compile(r"(^|/)test_[^/]*\.py$"),
        re.compile(r"^\s*(?:async )?def test_", re.MULTILINE),
    ),
    "bats": (re.compile(r"\.bats$"), re.compile(r"^@test ", re.MULTILINE)),
    "qml": (
        re.compile(r"(^|/)tst_[^/]*\.qml$"),
        re.compile(r"^\s*function test_", re.MULTILINE),
    ),
}


def tracked_files(repository):
    listing = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return [name for name in listing.stdout.split("\0") if name]


def test_counts(repository):
    counts = dict.fromkeys(SUITES, 0)
    for name in tracked_files(repository):
        for suite, (file_pattern, test_pattern) in SUITES.items():
            if not file_pattern.search(name):
                continue
            path = repository / name
            if path.is_file():
                counts[suite] += len(test_pattern.findall(path.read_text()))
    return counts


def budget_failures(counts, budgets):
    failures = []
    for suite, count in sorted(counts.items()):
        budget = budgets[suite]
        if count > budget:
            failures.append(
                f"{suite} has {count} tests and its budget is {budget}: remove a "
                f"test that pays less, never raise the budget ({POLICY})."
            )
        if count < budget:
            failures.append(
                f"{suite} shrank from {budget} to {count} tests; lower its budget "
                f"to {count} in {BUDGET_PATH.name}."
            )
    return failures


def main():
    counts = test_counts(REPOSITORY_ROOT)
    failures = budget_failures(counts, json.loads(BUDGET_PATH.read_text()))
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(f"Test budget check: OK ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
