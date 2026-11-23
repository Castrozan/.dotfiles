import ast
import os
import sys
import tempfile
from pathlib import Path

import coverage
from sandbox import sandboxed_pytest

WHOLE_FILE = (1, sys.maxsize)
FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


def function_level(context):
    return context.split("|")[0].split("[")[0]


def recorded_reach(root, data_path):
    data = coverage.CoverageData(basename=str(data_path))
    data.read()
    return {
        os.path.relpath(measured, root): {
            line: {function_level(context) for context in contexts if context}
            for line, contexts in data.contexts_by_lineno(measured).items()
        }
        for measured in data.measured_files()
    }


def reach_map(root, subtree, unit_files, timeout_seconds):
    with tempfile.TemporaryDirectory() as scratch:
        data_path = Path(scratch) / "coverage"
        sandboxed_pytest(
            root,
            [f"--cov={subtree}", "--cov-context=test", "--cov-report=", *unit_files],
            timeout_seconds,
            writable_directories=[scratch],
            extra_environment={"COVERAGE_FILE": str(data_path)},
        )
        return recorded_reach(root, data_path) if data_path.exists() else {}


def enclosing_range(tree, line):
    ranges = [
        (node.lineno, node.end_lineno)
        for node in ast.walk(tree)
        if isinstance(node, FUNCTION_NODES) and node.lineno <= line <= node.end_lineno
    ]
    return max(ranges, default=WHOLE_FILE)


def reaching(line_reach, line_range):
    first_line, last_line = line_range
    reached = set()
    for line, names in line_reach.items():
        if first_line <= line <= last_line:
            reached |= names
    return sorted(reached)
