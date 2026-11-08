import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

FILES_PLACEHOLDER = "{files}"
OUTPUT_TAIL_LINE_COUNT = 15


@dataclass(frozen=True)
class CheckOutcome:
    batch_name: str
    check_command: str
    passed: bool
    output_tail: str


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="swarm-batch-gate",
        description="Run every check command against every swarm batch's files and report each batch's verdict.",
    )
    parser.add_argument(
        "--batches",
        required=True,
        type=Path,
        help='JSON object mapping a batch name to its file list, e.g. {"batch-1": ["a.py", "b.py"]}.',
    )
    parser.add_argument(
        "--check",
        action="append",
        required=True,
        help="Shell command run once per batch; {files} expands to that batch's quoted files. Repeatable.",
    )
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-seconds", type=int, default=600)
    return parser.parse_args()


def read_batches(batches_path):
    batches = json.loads(batches_path.read_text())
    if (
        not isinstance(batches, dict)
        or not batches
        or not all(isinstance(files, list) for files in batches.values())
    ):
        raise SystemExit(
            f"{batches_path} must hold a non-empty JSON object of batch name to file list"
        )
    return {
        batch_name: [str(file) for file in files]
        for batch_name, files in batches.items()
    }


def command_for_batch(check_command, files):
    return check_command.replace(
        FILES_PLACEHOLDER, " ".join(shlex.quote(file) for file in files)
    )


def output_tail(text):
    return "\n".join(text.strip().splitlines()[-OUTPUT_TAIL_LINE_COUNT:])


def run_check(batch_name, files, check_command, working_directory, timeout_seconds):
    try:
        completed = subprocess.run(
            ["bash", "-c", command_for_batch(check_command, files)],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return CheckOutcome(
            batch_name, check_command, False, f"timed out after {timeout_seconds}s"
        )
    return CheckOutcome(
        batch_name,
        check_command,
        completed.returncode == 0,
        output_tail(completed.stdout + completed.stderr),
    )


def print_report(outcomes):
    for outcome in outcomes:
        verdict = "PASS" if outcome.passed else "FAIL"
        print(f"{verdict}  {outcome.batch_name}  {outcome.check_command}")
    for outcome in outcomes:
        if not outcome.passed:
            print(
                f"\n--- {outcome.batch_name}: {outcome.check_command}\n{outcome.output_tail}"
            )
    failed_count = sum(1 for outcome in outcomes if not outcome.passed)
    print(f"\n{len(outcomes) - failed_count} of {len(outcomes)} batch checks passed")


def main():
    arguments = parse_arguments()
    batches = read_batches(arguments.batches)
    outcomes = [
        run_check(
            batch_name, files, check_command, arguments.cwd, arguments.timeout_seconds
        )
        for batch_name, files in batches.items()
        for check_command in arguments.check
    ]
    print_report(outcomes)
    return 0 if all(outcome.passed for outcome in outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
