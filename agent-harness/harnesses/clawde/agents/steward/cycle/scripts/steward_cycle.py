import argparse
import fcntl
import json
import os
import sys
import time
from pathlib import Path

from cycle_actions import execute
from cycle_commands import CommandRunner
from cycle_configuration import CycleConfiguration
from cycle_decision import decide
from cycle_jobs import run_job
from cycle_observation import observe
from cycle_records import current_timestamp, read_record, remove_record, write_record
from cycle_validation_worker import validate_revision

REPEATED_ERRORS_BEFORE_ATTENTION = 3


def cycle_command() -> list[str]:
    return [sys.executable, str(Path(__file__).resolve())]


def publish(configuration: CycleConfiguration, report: dict) -> None:
    if configuration.dry_run:
        return
    write_record(configuration.decision_file, report)
    if report.get("attention"):
        write_record(configuration.attention_file, report["attention"])
    else:
        remove_record(configuration.attention_file)


def run_cycle(configuration: CycleConfiguration, runner: CommandRunner) -> dict:
    facts = observe(configuration, runner, time.time())
    decision = decide(facts)
    outcome = (
        ""
        if configuration.dry_run
        else execute(decision, facts, configuration, runner, cycle_command())
    )
    if not configuration.dry_run:
        remove_record(configuration.state_directory / "cycle-error.json")
    return {
        "observed": current_timestamp(),
        "dry_run": configuration.dry_run,
        "action": decision.action,
        "reason": decision.reason,
        "outcome": outcome,
        "attention": decision.attention,
        "head": facts.head,
        "upstream": facts.upstream,
        "behind": facts.behind,
        "ahead": facts.ahead,
    }


def error_report(configuration: CycleConfiguration, error: Exception) -> dict:
    error_file = configuration.state_directory / "cycle-error.json"
    previous = read_record(error_file) or {}
    detail = f"{type(error).__name__}: {error}"
    count = int(previous.get("count", 0)) + 1 if previous.get("detail") == detail else 1
    if not configuration.dry_run:
        write_record(error_file, {"detail": detail, "count": count})
    needs_attention = count >= REPEATED_ERRORS_BEFORE_ATTENTION
    return {
        "observed": current_timestamp(),
        "dry_run": configuration.dry_run,
        "action": "error",
        "reason": detail,
        "outcome": f"failed {count} cycles in a row",
        "attention": {"kind": "cycle-error", "detail": detail}
        if needs_attention
        else None,
    }


def run_guarded(configuration: CycleConfiguration, runner: CommandRunner) -> dict:
    configuration.state_directory.mkdir(parents=True, exist_ok=True)
    with configuration.lock_file.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"action": "skipped", "reason": "another cycle holds the lock"}
        try:
            report = run_cycle(configuration, runner)
        except Exception as error:
            report = error_report(configuration, error)
        publish(configuration, report)
        return report


def print_attention(configuration: CycleConfiguration) -> None:
    record = read_record(configuration.attention_file)
    if record:
        print(json.dumps(record, sort_keys=True))


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="steward-cycle")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser(
        "run", help="observe the checkout and take at most one step"
    )
    run.add_argument(
        "--dry-run", action="store_true", help="decide and print without acting"
    )
    commands.add_parser(
        "attention", help="print the failure that needs the steward agent, if any"
    )
    worker = commands.add_parser(
        "validate-revision", help="build one revision and record its verdict"
    )
    worker.add_argument("--revision", required=True)
    worker.add_argument("--attempt", type=int, required=True)
    job = commands.add_parser(
        "run-job", help="run a command while holding its job lock"
    )
    job.add_argument("--lock", type=Path, required=True)
    job.add_argument("job_command", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    if arguments.command == "run-job":
        return run_job(arguments.lock, arguments.job_command[1:])
    configuration = CycleConfiguration.from_settings(
        Path(os.environ["STEWARD_CYCLE_SETTINGS"]),
        dict(os.environ),
        getattr(arguments, "dry_run", False),
    )
    runner = CommandRunner()
    if arguments.command == "attention":
        print_attention(configuration)
        return 0
    if arguments.command == "validate-revision":
        validate_revision(configuration, runner, arguments.revision, arguments.attempt)
        return 0
    print(json.dumps(run_guarded(configuration, runner), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
