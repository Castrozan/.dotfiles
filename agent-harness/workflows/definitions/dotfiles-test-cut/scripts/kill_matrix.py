import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from source_mutants import source_mutants

FAILED_TEST = re.compile(
    r"^(?:FAILED|ERROR) (\S+?)(?:\[.*\])?(?: - .*)?$", re.MULTILINE
)
COLLECTED_TEST = re.compile(r"^(\S+::\S+?)(?:\[.*\])?$", re.MULTILINE)
GIT_TIMEOUT_SECONDS = 10
COLLECTION_TIMEOUT_SECONDS = 120


def tracked_python_files(root, subtree):
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--", subtree],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return [name for name in listing.stdout.split("\0") if name.endswith(".py")]


def is_test_support(name):
    return "__tests__/" in name or Path(name).name == "conftest.py"


def unit_test_files(names):
    return [
        name
        for name in names
        if "__tests__/unit/" in name and Path(name).name.startswith("test_")
    ]


def pytest_output(root, arguments, timeout_seconds):
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                *arguments,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired:
        return None
    return completed.stdout


def collected_tests(root, test_files):
    output = pytest_output(
        root, ["--collect-only", *test_files], COLLECTION_TIMEOUT_SECONDS
    )
    return sorted(set(COLLECTED_TEST.findall(output or "")))


def failing_tests(root, test_files, timeout_seconds):
    output = pytest_output(root, ["--tb=no", "-rfE", *test_files], timeout_seconds)
    if output is None:
        return None
    return sorted(set(FAILED_TEST.findall(output)))


def mutant_kills(root, source_name, test_files, options):
    source_path = root / source_name
    original_text = source_path.read_text()
    kills = []
    try:
        for description, mutated_text in source_mutants(
            original_text, options.mutants_per_file
        ):
            source_path.write_text(mutated_text)
            failed = failing_tests(root, test_files, options.run_timeout_seconds)
            kills.append(
                {
                    "mutant": f"{source_name} {description}",
                    "timed_out": failed is None,
                    "killed_by": failed or [],
                }
            )
    finally:
        source_path.write_text(original_text)
    return kills


def kill_matrix(root, subtree, options):
    names = tracked_python_files(root, subtree)
    test_files = unit_test_files(names)
    baseline_failures = failing_tests(root, test_files, options.run_timeout_seconds)
    if baseline_failures is None or baseline_failures:
        return {"error": "the unit tests do not pass before mutation", "mutants": []}
    sources = [name for name in names if not is_test_support(name)]
    mutants = [
        kill
        for source_name in sources[: options.maximum_source_files]
        for kill in mutant_kills(root, source_name, test_files, options)
    ]
    return {
        "error": "",
        "subtree": subtree,
        "tests": collected_tests(root, test_files),
        "sources_mutated": sources[: options.maximum_source_files],
        "sources_skipped": sources[options.maximum_source_files :],
        "mutants": mutants,
    }


def arguments():
    parser = argparse.ArgumentParser(
        description="Measure which unit tests of one subtree fail when its sources are mutated"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--subtree", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mutants-per-file", type=int, default=12)
    parser.add_argument("--maximum-source-files", type=int, default=12)
    parser.add_argument("--run-timeout-seconds", type=int, default=120)
    return parser.parse_args()


def main():
    options = arguments()
    matrix = kill_matrix(options.root.resolve(), options.subtree, options)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(matrix, indent=1) + "\n")
    print(json.dumps({"matrix_path": str(options.output), "error": matrix["error"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
