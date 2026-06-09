"""Edge-triggered heartbeat gate for the dotfiles steward agent.

Wakes the LLM only when the decision-relevant state changed since the last
wake. A non-clean state that the steward already surfaced and cannot advance -
a persistent non-fast-forward divergence holding human work in progress, a CI
run still failing on the same revision - keeps `attention_required` true every
tick, so a level-triggered gate would re-wake the model forever to re-derive the
same defer-and-idle. This gate fingerprints the actionable signals and fires
only on a change, so a steady benign state is surfaced once, not every tick.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

DECISION_FINGERPRINT_FIELDS = (
    "verdict",
    "head",
    "upstream",
    "behind",
    "ahead",
    "dirty",
    "inbox_unread",
)


def steward_workspace_directory() -> Path:
    return Path(
        os.environ.get("STEWARD_WORKSPACE_DIR", str(Path.home() / "clawde" / "steward"))
    )


def wake_fingerprint_file() -> Path:
    return steward_workspace_directory() / "state" / "last-heartbeat-wake-fingerprint"


def steward_status_command() -> list[str]:
    return [os.environ.get("STEWARD_STATUS_COMMAND", "steward-status")]


def collect_steward_status() -> dict:
    completed = subprocess.run(
        steward_status_command(),
        capture_output=True,
        text=True,
        timeout=180,
    )
    return json.loads(completed.stdout)


def decision_fingerprint(status: dict) -> str:
    relevant = {field: status.get(field) for field in DECISION_FINGERPRINT_FIELDS}
    relevant["continuous_integration_state"] = status.get(
        "continuous_integration", {}
    ).get("state")
    return json.dumps(relevant, sort_keys=True)


def read_previous_fingerprint() -> str | None:
    path = wake_fingerprint_file()
    return path.read_text() if path.is_file() else None


def store_fingerprint(fingerprint: str) -> None:
    path = wake_fingerprint_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fingerprint)


def clear_fingerprint() -> None:
    wake_fingerprint_file().unlink(missing_ok=True)


def main() -> int:
    status = collect_steward_status()
    if not status.get("attention_required"):
        clear_fingerprint()
        return 1
    current = decision_fingerprint(status)
    if current == read_previous_fingerprint():
        return 1
    store_fingerprint(current)
    return 0


if __name__ == "__main__":
    sys.exit(main())
