#!/usr/bin/env python3
"""nix-rebuild-reminder.py - Remind to rebuild after editing nix files."""

import json
import os
import sys

# File patterns that require rebuild
NIX_REBUILD_PATTERNS = [
    ".nix",           # All nix files
    "flake.lock",     # Flake lock file changes
]

# NixOS vs Home Manager file patterns
NIXOS_PATTERNS = [
    "nixos/",
    "system/",
    "hosts/",
    "configuration.nix",
    "hardware-configuration.nix",
]

HOME_MANAGER_PATTERNS = [
    "home/",
    "home-manager/",
    "home.nix",
    "dotfiles/",
]

def get_rebuild_command(file_path: str) -> str:
    """Determine appropriate rebuild command based on file path."""
    file_path_lower = file_path.lower()

    # Check for NixOS patterns
    if any(pattern in file_path_lower for pattern in NIXOS_PATTERNS):
        return "sudo nixos-rebuild switch"

    # Check for Home Manager patterns
    if any(pattern in file_path_lower for pattern in HOME_MANAGER_PATTERNS):
        return "home-manager switch"

    # Default for general nix files
    if file_path.endswith(".nix"):
        # Check if we're in a dotfiles-like structure
        if "home" in file_path_lower or "dotfiles" in os.getcwd().lower():
            return "home-manager switch"
        else:
            return "sudo nixos-rebuild switch (or home-manager switch)"

    return "nixos-rebuild switch or home-manager switch"

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Check if this is a file that requires rebuild
    needs_rebuild = False
    for pattern in NIX_REBUILD_PATTERNS:
        if file_path.endswith(pattern):
            needs_rebuild = True
            break

    if not needs_rebuild:
        sys.exit(0)

    rebuild_command = get_rebuild_command(file_path)

    # Special handling for flake.lock
    if file_path.endswith("flake.lock"):
        message = (
            "🔄 FLAKE LOCK UPDATED: Dependencies changed.\n"
            f"Run: {rebuild_command}"
        )
    else:
        # Regular nix file
        message = (
            f"⚙️  NIX CONFIG MODIFIED: {os.path.basename(file_path)}\n"
            f"Run: {rebuild_command}\n"
            "💡 Consider testing with --dry-run first"
        )

    output = {
        "continue": True,
        "systemMessage": message
    }
    print(json.dumps(output))

    sys.exit(0)

if __name__ == "__main__":
    main()