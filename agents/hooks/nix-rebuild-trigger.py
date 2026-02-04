#!/usr/bin/env python3
"""nix-rebuild-trigger.py - PostToolUse hook: remind to rebuild after nix file changes."""

import json
import os
import sys

# Nix file patterns that typically require a rebuild
NIX_FILE_PATTERNS = [
    ".nix",
]

# Paths that indicate system-level nix changes
SYSTEM_PATHS = [
    ".dotfiles",
    "/etc/nixos",
    "configuration.nix",
    "hardware-configuration.nix",
    "flake.nix",
    "flake.lock",
    "home.nix",
    "default.nix",
    "shell.nix",
    "/home/zanoni/.dotfiles",
]


def is_nix_file(path: str) -> bool:
    """Check if the file is a nix configuration file."""
    if not path:
        return False
    
    # Check extension
    for pattern in NIX_FILE_PATTERNS:
        if path.endswith(pattern):
            return True
    
    return False


def is_system_config(path: str) -> bool:
    """Check if this nix file is part of system/home configuration."""
    if not path:
        return False
    
    for system_path in SYSTEM_PATHS:
        if system_path in path:
            return True
    
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_output = data.get("tool_output", {})
    
    # Only process Edit and Write operations
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)

    # Get the file path from input
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
    
    if not file_path:
        sys.exit(0)

    # Check if it's a nix file
    if not is_nix_file(file_path):
        sys.exit(0)

    # Check if it's a system configuration file
    if is_system_config(file_path):
        output = {
            "continue": True,
            "systemMessage": (
                f"🔧 NIX FILE CHANGED: {os.path.basename(file_path)}\n"
                "Remember to rebuild to apply changes:\n"
                "  • System: nixos-rebuild switch --flake .#\n"
                "  • Home: home-manager switch --flake .#\n"
                "  • Both: ./bin/rebuild or use the /rebuild skill"
            )
        }
        print(json.dumps(output))
    else:
        # Generic nix file, lighter reminder
        output = {
            "continue": True,
            "systemMessage": (
                f"📝 Nix file modified: {os.path.basename(file_path)}\n"
                "Run `nix flake check` or rebuild if this affects system config."
            )
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
