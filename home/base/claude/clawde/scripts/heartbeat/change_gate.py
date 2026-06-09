import argparse
import os
import subprocess
import sys
from pathlib import Path

PROBE_TIMEOUT_SECONDS = 180


def default_state_file(label: str) -> Path:
    state_home = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return Path(state_home) / "clawde-heartbeat-change-gate" / label


def run_probe(probe_command: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["bash", "-c", probe_command],
        capture_output=True,
        text=True,
        timeout=PROBE_TIMEOUT_SECONDS,
    )
    return completed.returncode, completed.stdout.strip()


def read_stored_fingerprint(state_file: Path) -> str | None:
    return state_file.read_text() if state_file.is_file() else None


def store_fingerprint(state_file: Path, fingerprint: str) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(fingerprint)


def forget_fingerprint(state_file: Path) -> None:
    state_file.unlink(missing_ok=True)


def gate_fires(probe_command: str, state_file: Path) -> bool:
    return_code, fingerprint = run_probe(probe_command)
    if return_code != 0 or not fingerprint:
        forget_fingerprint(state_file)
        return False
    if fingerprint == read_stored_fingerprint(state_file):
        return False
    store_fingerprint(state_file, fingerprint)
    return True


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clawde-heartbeat-change-gate",
        description="Edge-triggered heartbeat gate any clawde agent can opt into. "
        "Run a probe command that prints the agent's current actionable fingerprint, "
        "and fire the tick (exit 0) only when that fingerprint differs from the last "
        "one fired. Empty probe output or a non-zero probe exit means nothing is "
        "actionable: skip the tick (exit 1) and forget the stored fingerprint so a "
        "later recurrence of the same state fires afresh. A steady actionable state is "
        "surfaced to the agent once, not every tick, so the agent spends no tokens "
        "re-deciding a state it already saw.",
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Stable agent identifier used to namespace the stored fingerprint.",
    )
    parser.add_argument(
        "--probe",
        required=True,
        help="Shell command printing the current actionable fingerprint, or nothing "
        "when the agent has no reason to wake.",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Override the fingerprint store path. Defaults to a per-label file under "
        "$XDG_STATE_HOME.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    state_file = (
        Path(arguments.state_file)
        if arguments.state_file
        else default_state_file(arguments.label)
    )
    return 0 if gate_fires(arguments.probe, state_file) else 1


if __name__ == "__main__":
    sys.exit(main())
