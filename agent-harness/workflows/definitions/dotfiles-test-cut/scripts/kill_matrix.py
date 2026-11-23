import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from reach_map import enclosing_range, reach_map, reaching
from source_mutants import source_mutants

FAILED_TEST = re.compile(
    r"^(?:FAILED|ERROR) (\S+?)(?:\[.*\])?(?: - .*)?$", re.MULTILINE
)
COLLECTED_TEST = re.compile(r"^(\S+::\S+?)(?:\[.*\])?$", re.MULTILINE)
GIT_TIMEOUT_SECONDS = 10
WHOLE_SUITE_TIMEOUT_SECONDS = 600
UNREACHED = {"reached_by": [], "killed_by": [], "timed_out": False}


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


def collected_tests(root, unit_files):
    output = pytest_output(
        root, ["--collect-only", *unit_files], WHOLE_SUITE_TIMEOUT_SECONDS
    )
    return sorted(set(COLLECTED_TEST.findall(output or "")))


def failing_tests(root, selected, timeout_seconds):
    output = pytest_output(root, ["--tb=no", "-rfE", *selected], timeout_seconds)
    if output is None:
        return None
    return sorted(set(FAILED_TEST.findall(output)))


def killers(failed, reached_by):
    return [
        name for name in reached_by if name in failed or name.split("::")[0] in failed
    ]


def measured_mutant(root, source_path, mutated_text, reached_by, options):
    if not reached_by:
        return UNREACHED
    source_path.write_text(mutated_text)
    failed = failing_tests(root, reached_by, options.run_timeout_seconds)
    return {
        "reached_by": reached_by,
        "killed_by": killers(failed or [], reached_by),
        "timed_out": failed is None,
    }


def mutant_kills(root, source_name, line_reach, options):
    source_path = root / source_name
    original_text = source_path.read_text()
    tree = ast.parse(original_text)
    records = []
    try:
        for line, description, mutated_text in source_mutants(
            original_text, options.mutants_per_file
        ):
            reached_by = reaching(line_reach, enclosing_range(tree, line))
            records.append(
                {"mutant": f"{source_name} {description}", "source": source_name}
                | measured_mutant(root, source_path, mutated_text, reached_by, options)
            )
    finally:
        source_path.write_text(original_text)
    return records


def kill_matrix(root, subtree, options):
    names = tracked_python_files(root, subtree)
    unit_files = unit_test_files(names)
    baseline_failures = failing_tests(root, unit_files, WHOLE_SUITE_TIMEOUT_SECONDS)
    if not unit_files or baseline_failures is None or baseline_failures:
        return {"error": "the unit tests do not pass before mutation", "mutants": []}
    reach = reach_map(root, subtree, unit_files, WHOLE_SUITE_TIMEOUT_SECONDS)
    sources = [name for name in names if not is_test_support(name)]
    reached_sources = [name for name in sources if reach.get(name)]
    return {
        "error": "",
        "subtree": subtree,
        "tests": collected_tests(root, unit_files),
        "sources_mutated": reached_sources,
        "sources_unreached": sorted(set(sources) - set(reached_sources)),
        "mutants": [
            record
            for source_name in reached_sources
            for record in mutant_kills(root, source_name, reach[source_name], options)
        ],
    }


def arguments():
    parser = argparse.ArgumentParser(
        description="Measure which unit tests of one subtree fail when its sources are mutated"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--subtree", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mutants-per-file", type=int, default=60)
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
