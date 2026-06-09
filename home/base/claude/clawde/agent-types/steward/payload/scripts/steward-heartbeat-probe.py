import json
import os
import subprocess
import sys

DECISION_FINGERPRINT_FIELDS = (
    "verdict",
    "head",
    "upstream",
    "behind",
    "ahead",
    "dirty",
    "inbox_unread",
)


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


def main() -> int:
    status = collect_steward_status()
    if not status.get("attention_required"):
        return 0
    sys.stdout.write(decision_fingerprint(status) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
