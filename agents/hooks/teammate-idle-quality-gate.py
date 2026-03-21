#!/usr/bin/env python3
import json
import subprocess
import sys


def get_staged_file_count(cwd: str) -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=5,
    )
    if result.returncode != 0:
        return 0
    lines = [line for line in result.stdout.strip().splitlines() if line]
    return len(lines)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("hook_event_name") != "TeammateIdle":
        sys.exit(0)

    cwd = data.get("cwd", ".")
    teammate_name = data.get("teammate_name", "teammate")

    try:
        staged_count = get_staged_file_count(cwd)
    except Exception:
        sys.exit(0)

    if staged_count > 0:
        print(
            f"{teammate_name}: {staged_count} staged file(s) not committed. "
            f"Commit staged changes before going idle.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
