import argparse
import json
import subprocess
import sys
from pathlib import Path

from kill_matrix import (
    WHOLE_SUITE_TIMEOUT_SECONDS,
    failing_tests,
    tracked_python_files,
    unit_test_files,
)
from source_mutants import EVERY_MUTANT, source_mutants

BUDGET_PATH = "repository/verification/quality/test-budget/budget.json"
BUDGET_CHECK = "repository/verification/quality/test-budget/check.py"
GIT_TIMEOUT_SECONDS = 30
BUDGET_CHECK_TIMEOUT_SECONDS = 60


def killed_by_source(matrix):
    grouped = {}
    for record in matrix["mutants"]:
        if record["killed_by"]:
            grouped.setdefault(record["source"], []).append(record)
    return grouped


def escaped_from_source(root, source_name, records, removed, options):
    source_path = root / source_name
    original_text = source_path.read_text()
    mutated_texts = {
        f"{source_name} {description}": mutated_text
        for _, description, mutated_text in source_mutants(
            original_text, options.mutants_per_file
        )
    }
    escaped = []
    try:
        for record in records:
            staying = [name for name in record["killed_by"] if name not in removed]
            source_path.write_text(mutated_texts[record["mutant"]])
            if (
                not staying
                or failing_tests(root, staying, options.run_timeout_seconds) == []
            ):
                escaped.append(record["mutant"])
    finally:
        source_path.write_text(original_text)
    return escaped


def escaped_mutants(root, matrix, removed, options):
    return [
        mutant
        for source_name, records in killed_by_source(matrix).items()
        for mutant in escaped_from_source(root, source_name, records, removed, options)
    ]


def budget_failure(root):
    checked = subprocess.run(
        [sys.executable, str(root / BUDGET_CHECK)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=BUDGET_CHECK_TIMEOUT_SECONDS,
    )
    return checked.stderr.strip() if checked.returncode else ""


def cut_failure(root, matrix, removed, options):
    unit_files = unit_test_files(tracked_python_files(root, matrix["subtree"]))
    existing = [name for name in unit_files if (root / name).exists()]
    if failing_tests(root, existing, WHOLE_SUITE_TIMEOUT_SECONDS) != []:
        return "the remaining unit tests do not pass"
    escaped = escaped_mutants(root, matrix, removed, options)
    if escaped:
        return f"{len(escaped)} mutants caught before now survive: {escaped[:5]}"
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
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--applied", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--mutants-per-file", type=int, default=EVERY_MUTANT)
    parser.add_argument("--run-timeout-seconds", type=int, default=120)
    return parser.parse_args()


def main():
    options = arguments()
    root = options.root.resolve()
    matrix = json.loads(options.matrix.read_text())
    removed = set(json.loads(options.applied.read_text())["removed"])
    failure = cut_failure(root, matrix, removed, options)
    if failure:
        restore(root, matrix["subtree"])
    print(
        json.dumps(
            {
                "kept": not failure,
                "patch_path": written_patch(root, options.patch),
                "detail": failure
                or "every mutant caught before the cut is still caught",
                "tests_before": len(matrix["tests"]),
                "tests_cut": 0 if failure else len(removed),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
