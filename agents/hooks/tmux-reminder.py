#!/usr/bin/env python3

import json
import os
import re
import sys

LONG_RUNNING_COMMAND_PATTERNS = [
    (r"^bundle\s+install", "bundle install can take a while"),
    (r"^ffmpeg\s+", "ffmpeg encoding can take a long time"),
    (r"^rsync\s+", "rsync transfers can be lengthy"),
    (r"^wget\s+.*-r", "recursive downloads can take hours"),
    (r"^curl\s+.*-O.*\.(iso|tar|zip|gz)", "large file downloads take time"),
]


def is_running_inside_tmux() -> bool:
    return bool(os.environ.get("TMUX"))


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    if is_running_inside_tmux():
        sys.exit(0)

    for pattern, reason in LONG_RUNNING_COMMAND_PATTERNS:
        if re.search(pattern, command.strip(), re.IGNORECASE):
            output = {
                "continue": True,
                "systemMessage": (
                    f"TMUX REMINDER: {reason}.\n"
                    "Consider running in tmux to prevent "
                    "losing progress if connection drops.\n"
                    "Start with: tmux new -s build  |  "
                    "Attach with: tmux attach -t build"
                ),
            }
            print(json.dumps(output))
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
