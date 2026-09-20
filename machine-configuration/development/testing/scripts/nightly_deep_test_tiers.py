import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from nightly_cleanup import (
    artifact_directories_under,
    prune_docker_build_leftovers_the_run_did_not_reuse,
)
from steward_inbox import leave_message_in_the_steward_inbox

DOTFILES_DIRECTORY = Path.home() / ".dotfiles"
LOG_DIRECTORY = Path.home() / ".local" / "state" / "dotfiles-nightly-tests"
LOG_FILE_NAME = "nightly-deep-test-tiers.log"
DEEP_TIER_FLAGS = (
    "--integration-scripts",
    "--runtime",
    "--perf",
    "--integration",
    "--e2e",
)
TIER_SKIPPED_STATUS = 77
IDLE_WINDOW_FIRST_HOUR = 2
IDLE_WINDOW_LAST_HOUR = 5
ARTIFACT_FREE_ENVIRONMENT = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTEST_ADDOPTS": "-p no:cacheprovider",
}

EXIT_CODE_A_TIER_FAILED = 1
EXIT_CODE_CANNOT_RUN = 2
CANNOT_RUN_VERDICT = "FAILED to run: dotfiles-test is not on PATH, so no tier can run"
STEWARD_INBOX_SENDER = "nightly-deep-tiers"


def log_file_path() -> Path:
    return LOG_DIRECTORY / LOG_FILE_NAME


def open_log_file():
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    return log_file_path().open("w")


def current_hour() -> int:
    return datetime.now().hour


def is_inside_the_idle_window(hour: int) -> bool:
    return IDLE_WINDOW_FIRST_HOUR <= hour <= IDLE_WINDOW_LAST_HOUR


def untracked_paths_in_repository() -> set[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=DOTFILES_DIRECTORY,
        capture_output=True,
        text=True,
    )
    return {
        line[3:]
        for line in completed.stdout.splitlines()
        if line.startswith("?? ") or line.startswith("!! ")
    }


def environment_that_leaves_no_cache() -> dict:
    environment = dict(os.environ)
    environment.update(ARTIFACT_FREE_ENVIRONMENT)
    return environment


def run_tier(tier_flag: str, log) -> int:
    log.write(f"=== dotfiles-test {tier_flag} ===\n")
    log.flush()
    completed = subprocess.run(
        ["dotfiles-test", tier_flag],
        cwd=DOTFILES_DIRECTORY,
        env=environment_that_leaves_no_cache(),
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    log.write(f"=== {tier_flag} exited {completed.returncode} ===\n")
    log.flush()
    return completed.returncode


def run_every_tier_reporting_all_failures(log) -> tuple[list[str], list[str]]:
    failed_tiers = []
    skipped_tiers = []
    for tier_flag in DEEP_TIER_FLAGS:
        status = run_tier(tier_flag, log)
        if status == TIER_SKIPPED_STATUS:
            skipped_tiers.append(tier_flag)
        elif status != 0:
            failed_tiers.append(tier_flag)
    return failed_tiers, skipped_tiers


def remove_generated_cache_directories(log) -> None:
    for directory in artifact_directories_under(DOTFILES_DIRECTORY):
        shutil.rmtree(directory, ignore_errors=True)
        log.write(f"removed cache directory {directory}\n")


def report_paths_the_run_left_behind(paths_before: set[str], log) -> None:
    leftovers = sorted(untracked_paths_in_repository() - paths_before)
    if not leftovers:
        log.write("no untracked path survived the run\n")
        return
    log.write(
        "the run left untracked paths behind, remove them by hand if they are test "
        "artifacts and not parallel work:\n"
    )
    for leftover in leftovers:
        log.write(f"  leftover {leftover}\n")


def night_verdict(failed_tiers: list[str], skipped_tiers: list[str]) -> str:
    if failed_tiers:
        verdict = f"FAILED tiers: {', '.join(failed_tiers)}"
    elif len(skipped_tiers) == len(DEEP_TIER_FLAGS):
        verdict = "FAILED to prove anything: every deep tier skipped"
    else:
        passed = [flag for flag in DEEP_TIER_FLAGS if flag not in skipped_tiers]
        verdict = f"every deep tier passed: {', '.join(passed)}"
    if skipped_tiers and not verdict.startswith("FAILED to prove"):
        verdict += f". SKIPPED, proving nothing: {', '.join(skipped_tiers)}"
    return verdict


def leave_the_failed_night_in_the_steward_inbox(verdict: str, log) -> None:
    message_file = leave_message_in_the_steward_inbox(
        STEWARD_INBOX_SENDER,
        f"Nightly deep tiers on {socket.gethostname()}: {verdict}. "
        f"Log: {log_file_path()}. Treat it like red CI.",
    )
    if message_file is None:
        log.write("no steward workspace on this machine, so nobody is told\n")
        return
    log.write(f"left the failed night in the steward inbox as {message_file.name}\n")


def run_the_deep_tiers_and_clean_up() -> int:
    with open_log_file() as log:
        paths_before = untracked_paths_in_repository()
        failed_tiers, skipped_tiers = run_every_tier_reporting_all_failures(log)
        remove_generated_cache_directories(log)
        prune_docker_build_leftovers_the_run_did_not_reuse(log)
        report_paths_the_run_left_behind(paths_before, log)

        verdict = night_verdict(failed_tiers, skipped_tiers)
        if failed_tiers or len(skipped_tiers) == len(DEEP_TIER_FLAGS):
            leave_the_failed_night_in_the_steward_inbox(verdict, log)
            log.write(f"{verdict}\n")
            return EXIT_CODE_A_TIER_FAILED

        log.write(f"{verdict}\n")
        return 0


def main() -> int:
    forced = "--force" in sys.argv[1:]

    if not forced and not is_inside_the_idle_window(current_hour()):
        print(
            f"hour {current_hour()} is outside the "
            f"{IDLE_WINDOW_FIRST_HOUR}:00 to {IDLE_WINDOW_LAST_HOUR}:59 idle window, "
            f"so these tiers stay off a machine somebody is using; pass --force to "
            f"run them anyway",
            file=sys.stderr,
        )
        return 0

    if shutil.which("dotfiles-test") is None:
        with open_log_file() as log:
            leave_the_failed_night_in_the_steward_inbox(CANNOT_RUN_VERDICT, log)
            log.write(f"{CANNOT_RUN_VERDICT}\n")
        print(CANNOT_RUN_VERDICT, file=sys.stderr)
        return EXIT_CODE_CANNOT_RUN

    return run_the_deep_tiers_and_clean_up()


if __name__ == "__main__":
    sys.exit(main())
