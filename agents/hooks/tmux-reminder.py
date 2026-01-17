#!/usr/bin/env python3
"""
Tmux Reminder Hook
==================
Reminds to use tmux for long-running commands when not in a tmux session.
Suggests using /tmux skill for session management.
"""

import json
import os
import re
import sys

# Commands that typically run for a long time
LONG_RUNNING_PATTERNS = [
    # Package managers
    r"^(npm|pnpm|yarn)\s+(run\s+)?(start|dev|serve|watch|build|test)",
    r"^(cargo)\s+(run|build|test|bench)",
    r"^(pytest|python\s+-m\s+pytest)",
    r"^(make)\s*(build|test|all|install)?",

    # Nix
    r"^(nix-build|nix\s+build|nixos-rebuild|home-manager\s+switch)",
    r"^(nix\s+develop|nix-shell)",

    # Docker
    r"^(docker|docker-compose|podman)\s+(build|up|run)",

    # Dev servers
    r"^(webpack|vite|next|nuxt|gatsby)\s*(dev|start|build)?",
    r"^(turbo|nx)\s+(run|build|test|dev)",

    # Testing
    r"^(jest|vitest|mocha|ava)",
    r"^(go\s+test|go\s+build)",
    r"^(mvn|gradle)\s+(build|test|run)",

    # Other long operations
    r"^(rsync|scp|wget|curl)\s+.*(-r|--recursive)",
    r"^(find|rg|grep)\s+/",  # Searching from root
]


def is_long_running(command: str) -> bool:
    """Check if command is likely to be long-running."""
    for pattern in LONG_RUNNING_PATTERNS:
        if re.search(pattern, command.strip(), re.IGNORECASE):
            return True
    return False


def in_tmux() -> bool:
    """Check if we're inside a tmux session."""
    return bool(os.environ.get("TMUX"))


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    if is_long_running(command) and not in_tmux():
        output = {
            "continue": True,
            "systemMessage": (
                "TMUX REMINDER: This command may run for a long time. "
                "Consider using tmux (/tmux skill) to:\n"
                "- Keep the process running if connection drops\n"
                "- Monitor output in a dedicated pane\n"
                "- Easily switch between tasks"
            )
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
