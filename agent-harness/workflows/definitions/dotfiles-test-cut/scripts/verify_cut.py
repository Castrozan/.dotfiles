import argparse
import json
import subprocess
import sys
from pathlib import Path

from kill_matrix import kill_matrix

BUDGET_PATH = "repository/verification/quality/test-budget/budget.json"
BUDGET_CHECK = "repository/verification/quality/test-budget/check.py"
GIT_TIMEOUT_SECONDS = 30
BUDGET_CHECK_TIMEOUT_SECONDS = 60


def killed_mutants(matrix):
    return {mutant["mutant"] for mutant in matrix["mutants"] if mutant["killed_by"]}


def budget_failure(root):
    checked = subprocess.run(
        [sys.executable, str(root / BUDGET_CHECK)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=BUDGET_CHECK_TIMEOUT_SECONDS,
    )
    return checked.stderr.strip() if checked.returncode else ""


def cut_failure(root, before, after):
    if after["error"]:
        return after["error"]
    escaped = sorted(killed_mutants(before) - killed_mutants(after))
    if escaped:
        return (
            f"{len(escaped)} mutants the suite caught before now survive: {escaped[:5]}"
        )
    return budget_failure(root)


def restore(root, subtree):
    subprocess.run(
        ["git", "checkout", "--", subtree, BUDGET_PATH],
        cwd=root,
        check=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )


def written_patch(root, patch_path):
    difference = subprocess.run(
        ["git", "diff"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    patch_path.write_text(difference.stdout)
    return str(patch_path)


def arguments():
    parser = argparse.ArgumentParser(
        description="Keep a test cut only when every mutant caught before it is still caught"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--subtree", required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--mutants-per-file", type=int, default=40)
    parser.add_argument("--maximum-source-files", type=int, default=12)
    parser.add_argument("--run-timeout-seconds", type=int, default=120)
    return parser.parse_args()


def main():
    options = arguments()
    root = options.root.resolve()
    before = json.loads(options.matrix.read_text())
    after = kill_matrix(root, options.subtree, options)
    failure = cut_failure(root, before, after)
    if failure:
        restore(root, options.subtree)
    print(
        json.dumps(
            {
                "kept": not failure,
                "patch_path": written_patch(root, options.patch),
                "detail": failure
                or "every mutant caught before the cut is still caught",
                "tests_before": len(before["tests"]),
                "tests_after": len(after.get("tests", [])),
                "mutants_killed": len(killed_mutants(after)),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
