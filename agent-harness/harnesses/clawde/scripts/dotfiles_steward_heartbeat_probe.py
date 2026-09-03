import os
import subprocess
import sys
from pathlib import Path

NIGHTLY_LOG_FILE = (
    Path.home()
    / ".local"
    / "state"
    / "dotfiles-nightly-tests"
    / "nightly-deep-test-tiers.log"
)
FAILED_NIGHT_PREFIX = "FAILED"
FINGERPRINT_SEPARATOR = " | "
UPSTREAM_PROBE_TIMEOUT_SECONDS = 240


def upstream_probe_command() -> list[str]:
    return [
        os.environ.get("STEWARD_HEARTBEAT_PROBE_COMMAND", "steward-heartbeat-probe")
    ]


def upstream_fingerprint() -> str:
    completed = subprocess.run(
        upstream_probe_command(),
        capture_output=True,
        text=True,
        timeout=UPSTREAM_PROBE_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def nightly_log_file() -> Path:
    return Path(os.environ.get("DOTFILES_NIGHTLY_LOG_FILE", NIGHTLY_LOG_FILE))


def last_line_of(path: Path) -> str:
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return lines[-1] if lines else ""


def failed_night_fingerprint() -> str:
    log_file = nightly_log_file()
    if not log_file.is_file():
        return ""
    verdict = last_line_of(log_file)
    if not verdict.startswith(FAILED_NIGHT_PREFIX):
        return ""
    return (
        f"nightly deep tiers: {verdict} (log written {int(log_file.stat().st_mtime)})"
    )


def main() -> int:
    fingerprints = [
        fingerprint
        for fingerprint in (upstream_fingerprint(), failed_night_fingerprint())
        if fingerprint
    ]
    if not fingerprints:
        return 0
    sys.stdout.write(FINGERPRINT_SEPARATOR.join(fingerprints) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
