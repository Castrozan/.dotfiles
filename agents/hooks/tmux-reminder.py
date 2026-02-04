#!/usr/bin/env python3
"""tmux-reminder.py - Remind to use tmux for long-running commands."""

import json
import os
import re
import sys

# Commands that typically take a long time to run
LONG_RUNNING_PATTERNS = [
    (r"^npm\s+(install|ci|build|run build)", "npm operations can take minutes"),
    (r"^yarn\s+(install|build)", "yarn operations can take minutes"),
    (r"^pnpm\s+(install|build)", "pnpm operations can take minutes"),
    (r"^cargo\s+(build|test|clippy)", "cargo builds can be slow"),
    (r"^pytest\s+", "test suites can run for a long time"),
    (r"^make\s+", "make builds can take a while"),
    (r"^cmake\s+", "cmake configuration can be slow"),
    (r"^docker\s+(build|pull|push)", "docker operations can be slow"),
    (r"^nix\s+(build|develop|flake)", "nix builds can take a long time"),
    (r"^nixos-rebuild\s+", "nixos-rebuild can take several minutes"),
    (r"^home-manager\s+switch", "home-manager switch can take a while"),
    (r"^\./bin/rebuild", "rebuild script can take several minutes"),
    (r"^pip\s+install", "pip installs can be slow"),
    (r"^bundle\s+install", "bundle install can take a while"),
    (r"^mvn\s+(clean|compile|package|install)", "maven builds are typically slow"),
    (r"^gradle\s+", "gradle builds can be slow"),
    (r"^ffmpeg\s+", "ffmpeg encoding can take a long time"),
    (r"^rsync\s+", "rsync transfers can be lengthy"),
    (r"^wget\s+.*-r", "recursive downloads can take hours"),
    (r"^curl\s+.*-O.*\.(iso|tar|zip|gz)", "large file downloads take time"),
]


def is_in_tmux() -> bool:
    """Check if currently running inside tmux."""
    return bool(os.environ.get("TMUX"))


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    # Skip if already in tmux
    if is_in_tmux():
        sys.exit(0)

    # Check for long-running patterns
    for pattern, reason in LONG_RUNNING_PATTERNS:
        if re.search(pattern, command.strip(), re.IGNORECASE):
            output = {
                "continue": True,
                "systemMessage": (
                    f"💡 TMUX REMINDER: {reason}.\n"
                    "Consider running in tmux to prevent losing progress if connection drops.\n"
                    "Start with: tmux new -s build  |  Attach with: tmux attach -t build"
                )
            }
            print(json.dumps(output))
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
