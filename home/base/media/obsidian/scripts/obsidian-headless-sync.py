#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

LOCK_REFRESH_OBSERVATION_WINDOW_SECONDS = 5.0
SYNC_ATTEMPT_LIMIT = 8
SYNC_GRACEFUL_TIMEOUT = "240s"
SYNC_KILL_AFTER = "30s"
LOCK_UNAVAILABLE_MESSAGE = "Another sync instance is already running for this vault."


def required_environment_value(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"{name} is not set", file=sys.stderr)
        raise SystemExit(1)
    return value


def lock_modification_time(lock_path: Path) -> int | None:
    try:
        return lock_path.stat().st_mtime_ns
    except OSError:
        return None


def another_sync_is_still_refreshing_the_lock(lock_path: Path) -> bool:
    before = lock_modification_time(lock_path)
    if before is None:
        return False
    time.sleep(LOCK_REFRESH_OBSERVATION_WINDOW_SECONDS)
    after = lock_modification_time(lock_path)
    return after is not None and after != before


def discard_the_abandoned_lock(lock_path: Path) -> None:
    shutil.rmtree(lock_path, ignore_errors=True)


def run_one_sync_attempt(
    timeout_binary: str, ob_binary: str, vault_path: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            timeout_binary,
            "--signal=TERM",
            f"--kill-after={SYNC_KILL_AFTER}",
            SYNC_GRACEFUL_TIMEOUT,
            ob_binary,
            "sync",
            "--path",
            vault_path,
        ],
        capture_output=True,
        text=True,
    )


def lost_the_lock_verification_race(completed: subprocess.CompletedProcess) -> bool:
    return LOCK_UNAVAILABLE_MESSAGE in f"{completed.stdout}{completed.stderr}"


def relay_sync_output(completed: subprocess.CompletedProcess) -> None:
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)


def main() -> int:
    node_bin_dir = required_environment_value("NODE_BIN_DIR")
    npm_prefix = required_environment_value("NPM_PREFIX")
    vault_path = required_environment_value("VAULT_PATH")
    timeout_binary = required_environment_value("TIMEOUT_BIN")

    os.environ["PATH"] = f"{node_bin_dir}:{os.environ.get('PATH', '')}"
    os.environ["NPM_CONFIG_PREFIX"] = npm_prefix

    ob_binary = Path(npm_prefix) / "bin" / "ob"
    if not os.access(ob_binary, os.X_OK):
        print(
            "obsidian-headless not installed. Run 'ob --version' to trigger install.",
            file=sys.stderr,
        )
        return 1

    lock_path = Path(vault_path) / ".obsidian" / ".sync.lock"

    for attempt in range(1, SYNC_ATTEMPT_LIMIT + 1):
        if another_sync_is_still_refreshing_the_lock(lock_path):
            print("Another sync is actively refreshing the lock. Skipping this pass.")
            return 0

        discard_the_abandoned_lock(lock_path)
        completed = run_one_sync_attempt(timeout_binary, str(ob_binary), vault_path)
        relay_sync_output(completed)

        if completed.returncode == 0:
            return 0
        if not lost_the_lock_verification_race(completed):
            return completed.returncode

        print(
            f"Lock verification race lost on attempt {attempt} of "
            f"{SYNC_ATTEMPT_LIMIT}; discarding the orphaned lock and retrying."
        )

    print(
        f"Gave up after {SYNC_ATTEMPT_LIMIT} attempts lost to the lock verification "
        f"race.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
