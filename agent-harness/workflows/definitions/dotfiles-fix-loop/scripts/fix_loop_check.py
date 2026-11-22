import argparse
import hashlib
import json
import re
import shlex
import sys
from pathlib import Path

from fix_loop_checkout import change_diff, changed_paths, git, run_program, run_shell

FORMATTERS = {".py": ("ruff", "format"), ".nix": ("nixfmt",)}
VOLATILE_TEXT = re.compile(r"\b\d+(\.\d+)?\s?(ms|s|sec|seconds)\b|0x[0-9a-f]+")
SIGNATURE_LENGTH = 16


def format_problems(root: Path, paths: list[str]) -> list[str]:
    problems = []
    for path in paths:
        formatter = FORMATTERS.get(Path(path).suffix)
        if formatter is None or not (root / path).is_file():
            continue
        formatted = run_program(root, [*formatter, path])
        if formatted.exit_code:
            problems.append(f"{' '.join(formatter)} {path}:\n{formatted.output}")
    return problems


def lint_problems(root: Path, lint_command: str, paths: list[str]) -> list[str]:
    existing = [path for path in paths if (root / path).exists()]
    if not lint_command or not existing:
        return []
    linted = run_program(root, [*shlex.split(lint_command), *existing])
    return [f"{lint_command}:\n{linted.output}"] if linted.exit_code else []


def commit_problems(root: Path, base_revision: str) -> list[str]:
    head = git(root, "rev-parse", "HEAD").strip()
    if head == base_revision:
        return []
    return [f"HEAD moved from {base_revision} to {head}: the workflow owns the commit"]


def failure_signature(passed: bool, failure_text: str) -> str:
    if passed:
        return ""
    normalized = VOLATILE_TEXT.sub("", failure_text)
    return hashlib.sha256(normalized.encode()).hexdigest()[:SIGNATURE_LENGTH]


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fix-loop-check",
        description=(
            "Format the files the fixer changed, run the lint gate and the scoped "
            "test, and write their logs and the change diff as artifacts."
        ),
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--test-command", required=True)
    parser.add_argument("--lint-command", default="")
    parser.add_argument("--artifacts", type=Path, required=True)
    return parser.parse_args(command_line_arguments)


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    root, artifacts = arguments.root, arguments.artifacts
    base_revision = (artifacts / "base-revision").read_text().strip()
    paths = changed_paths(root)
    gate_problems = [
        *commit_problems(root, base_revision),
        *format_problems(root, paths),
        *lint_problems(root, arguments.lint_command, paths),
    ]
    tested = run_shell(root, arguments.test_command)
    gate_log = "\n".join(gate_problems)
    passed = tested.exit_code == 0 and not gate_problems
    (artifacts / "test.log").write_text(tested.output)
    (artifacts / "gate.log").write_text(gate_log)
    (artifacts / "change.diff").write_text(change_diff(root, base_revision))
    report = {
        "passed": passed,
        "tests_passed": tested.exit_code == 0,
        "gates_passed": not gate_problems,
        "failure_signature": failure_signature(passed, tested.output + gate_log),
        "changed_files": changed_paths(root),
    }
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
