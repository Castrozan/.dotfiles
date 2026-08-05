import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DOTFILES_DIRECTORY = Path.home() / ".dotfiles"
LOG_DIRECTORY = Path.home() / ".local" / "state" / "dotfiles-nightly-tests"
LOG_FILE_NAME = "nightly-deep-test-tiers.log"
DEEP_TIER_FLAGS = ("--integration-scripts", "--runtime")
IDLE_WINDOW_FIRST_HOUR = 2
IDLE_WINDOW_LAST_HOUR = 5
ARTIFACT_DIRECTORY_NAMES = frozenset({".pytest_cache", ".ruff_cache", "__pycache__"})
PRUNED_DIRECTORY_NAMES = frozenset({".git", ".worktrees", "node_modules", "result"})
ARTIFACT_FREE_ENVIRONMENT = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTEST_ADDOPTS": "-p no:cacheprovider",
}

EXIT_CODE_A_TIER_FAILED = 1
EXIT_CODE_CANNOT_RUN = 2


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


def run_every_tier_reporting_all_failures(log) -> list[str]:
    failed_tiers = []
    for tier_flag in DEEP_TIER_FLAGS:
        if run_tier(tier_flag, log) != 0:
            failed_tiers.append(tier_flag)
    return failed_tiers


def artifact_directories_under(root: Path) -> list[Path]:
    found = []
    for directory, subdirectories, _ in os.walk(root):
        subdirectories[:] = [
            name for name in subdirectories if name not in PRUNED_DIRECTORY_NAMES
        ]
        for name in list(subdirectories):
            if name in ARTIFACT_DIRECTORY_NAMES:
                found.append(Path(directory) / name)
                subdirectories.remove(name)
    return found


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


def run_the_deep_tiers_and_clean_up() -> int:
    with open_log_file() as log:
        paths_before = untracked_paths_in_repository()
        failed_tiers = run_every_tier_reporting_all_failures(log)
        remove_generated_cache_directories(log)
        report_paths_the_run_left_behind(paths_before, log)

        if failed_tiers:
            log.write(f"FAILED tiers: {', '.join(failed_tiers)}\n")
            return EXIT_CODE_A_TIER_FAILED

        log.write(f"every deep tier passed: {', '.join(DEEP_TIER_FLAGS)}\n")
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
        print("dotfiles-test is not on PATH, so no tier can run", file=sys.stderr)
        return EXIT_CODE_CANNOT_RUN

    return run_the_deep_tiers_and_clean_up()


if __name__ == "__main__":
    sys.exit(main())
